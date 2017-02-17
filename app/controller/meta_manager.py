#!/usr/bin/env python
#encoding=utf-8
from tornado.options import options
import tornado.ioloop
import logging
from app.dbo.metadata import DboMetadata
from app.dbo.pool import DboPoolSubscriber
from app.lib import utils
from app.lib import thumbnail
import json
import sqlite3
import os

class MetaManager():
    '''!Metadata API Controller'''
    dbo_metadata = None
    account = None
    poolstorage = None
    poolid = None
    poolname = None
    can_edit = False
    path = None
    real_path = None
    db_path = None

    def __init__(self, sql_client, current_user, path):
        self.path = path
        self.account = current_user['account']
        self.poolid = current_user['poolid']
        if not self.poolid is None:
            # default access user-home.
            self.poolname = ""
            self.can_edit = True

        if len(path) > 1:
            # query share_folder
            pool_subscriber_dbo = DboPoolSubscriber(sql_client)
            pool_dict = pool_subscriber_dbo.find_share_poolid(self.account, path)
            if not pool_dict is None:
                self.poolid = pool_dict['poolid']
                self.poolname = pool_dict['poolname']
                # share folder under repo co-owner.
                self.can_edit = False
                if pool_dict['can_edit'] == 1:
                    self.can_edit = True

        if not self.poolid is None:
            self.poolstorage = '%s/storagepool/%s' % (options.storage_access_point,self.poolid)
            #logging.info('options.storage_access_point %s' % (options.storage_access_point))
            #logging.info('poolstorage %s' % (self.poolstorage))
            if self.dbo_metadata  is None:
                metadata_conn = self.open_metadata_db(self.poolid)
                self.dbo_metadata = DboMetadata(metadata_conn)

            self.db_path = path
            if len(path) > 0:
                self.db_path = path[len(self.poolname):]
            self.real_path = os.path.join(self.poolstorage, self.db_path[1:])
            #logging.info('user query metadata path:%s, at real path: %s' % (path, self.real_path))

    # open database.
    #[TODO] multi-database solution.
    #def open_metadata(self, poolid):
    def open_metadata_db(self, poolid):
        #if not poolid is None:
            #db_path = '%s/metadata/%s/metadata.db' % (options.storage_access_point,poolid)
            #logging.info("owner metadata poolid: %s ... ", db_path)
            #client = sqlite3.connect(db_path)
        db_path = '%s/metadata.db' % (options.storage_access_point)
        #logging.info("open metadata poolid: %s ... ", db_path)
        client = sqlite3.connect(db_path)
        return client


    def get_path(self, poolid=None, path=None):
        if poolid is None:
            poolid = self.poolid
        if path is None:
            path = self.db_path

        current_metadata = self.dbo_metadata.get_metadata(poolid, path)
        if not current_metadata is None:
            current_metadata = self.convert_for_dropboxlike_dict(current_metadata)
        return current_metadata

    def list_folder(self, poolid=None, path=None):
        if poolid is None:
            poolid = self.poolid
        if path is None:
            path = self.db_path

        metadata_dic = {}
        dic_children = self.dbo_metadata.list_folder(poolid, path)
        contents = []

        # for small case used.
        for item in dic_children:
            contents.append(self.convert_for_dropboxlike_dict(item))
        metadata_dic['entries']=contents
        
        metadata_dic['cursor']=utils.get_timestamp()
        #[TOOD]: paging metadata
        metadata_dic['has_more']=False

        #print 'dic_current:%s' % (metadata_dic)
        #self.write(metadata_dic)

        # for big data used. (but, seems speed the same.)
        '''
        metadata_dic['contents']=contents
        delimiter = '\"contents\": ['
        #body = "{}".format(metadata_dic)
        body = json.dumps(metadata_dic)
        body_item = body.split(delimiter)
        self.write(body_item[0]+delimiter)
        dic_children_count = len(dic_children)
        if dic_children_count > 0:
            iPos = 0
            for item in dic_children:
                iPos += 1
                self.write(json.dumps(self.convert_for_dropboxlike_dict(item)))
                if iPos < dic_children_count:
                    self.write(",")
        self.write(body_item[1])
        '''

        return metadata_dic

    def convert_for_dropboxlike_dict(self, tmp_dict):
        out_dic = None
        if not tmp_dict is None:
            out_dic = {}
            out_dic['id'] = tmp_dict['doc_id']
            out_dic['name'] = tmp_dict['name']
            out_dic['path'] = tmp_dict['path']
            
            #out_dic['permission'] = "{"write": True}"ll
            out_dic['permission'] = 'r'
            if self.can_edit:
                out_dic['permission'] = 'rw'
            
            out_dic['type'] = ("folder" if tmp_dict['is_dir']==1 else "file")
            if tmp_dict['is_dir']==0:
                out_dic['size'] = tmp_dict['size']
                out_dic['rev'] = tmp_dict['rev']
                out_dic['content_hash'] = tmp_dict['content_hash']
                out_dic['client_modified'] = tmp_dict['client_modified']
                out_dic['server_modified'] = tmp_dict['server_modified']
        return out_dic


    def add_metadata(self, size=0, rev=None, client_modified=None, is_dir=0, content_hash=None):
        in_dic = {}
        in_dic['poolid'] = self.poolid
        in_dic['path'] = self.db_path

        in_dic['rev'] = rev
        in_dic['size'] = size
        if client_modified is None:
            client_modified = utils.get_timestamp()
        in_dic['client_modified'] = client_modified
        in_dic['is_dir'] = is_dir
        in_dic['content_hash'] = content_hash
        in_dic['editor'] = self.account
        in_dic['owner'] = self.account

        check_metadata = self.get_path()
        if not check_metadata is None:
            # [TODO]: handle special case: same path insert twice, it is conflict.
            ret = self.delete_metadata(current_metadata=metadata)

        ret, current_metadata, errorMessage = self.dbo_metadata.insert(in_dic)
        if not current_metadata is None:
            current_metadata = self.convert_for_dropboxlike_dict(current_metadata)
            if current_metadata['type']=="file":
                tornado.ioloop.IOLoop.instance().add_callback(self.add_thumbnail,current_metadata)

        return ret, current_metadata, errorMessage

    def move_metadata(self, from_poolid, from_path, rev=None, size=None, client_modified=None, is_dir=None, content_hash=None):
        in_dic = {}
        in_dic['old_poolid'] = from_poolid
        in_dic['old_path'] = from_path
        in_dic['poolid'] = self.poolid
        in_dic['path'] = self.db_path

        if not rev is None:
            in_dic['rev'] = rev 
        if not size is None:
            in_dic['size'] = size
        if not client_modified is None:
            in_dic['client_modified'] = client_modified 
        if not is_dir is None:
            in_dic['is_dir'] = is_dir
        if not content_hash is None:
            in_dic['content_hash'] = content_hash

        in_dic['editor'] = self.account

        ret, current_metadata, errorMessage = self.dbo_metadata.update(in_dic)
        if not current_metadata is None:
            current_metadata = self.convert_for_dropboxlike_dict(current_metadata)
            
            # only need update current node instaed of full sub-tree.
            if current_metadata['type']=="file":
                tornado.ioloop.IOLoop.instance().add_callback(self.add_thumbnail,current_metadata)

        return ret, current_metadata, errorMessage

    def copy_metadata(self, from_poolid, from_path, rev=None, size=None, client_modified=None, is_dir=None, content_hash=None):
        in_dic = {}
        in_dic['old_poolid'] = from_poolid
        in_dic['old_path'] = from_path
        in_dic['poolid'] = self.poolid
        in_dic['path'] = self.db_path

        if not rev is None:
            in_dic['rev'] = rev 
        if not size is None:
            in_dic['size'] = size
        if not client_modified is None:
            in_dic['client_modified'] = client_modified 
        if not is_dir is None:
            in_dic['is_dir'] = is_dir
        if not content_hash is None:
            in_dic['content_hash'] = content_hash

        in_dic['editor'] = self.account

        ret, current_metadata, errorMessage = self.dbo_metadata.copy(in_dic)
        if not current_metadata is None:
            current_metadata = self.convert_for_dropboxlike_dict(current_metadata)
            # no matter file or folder should scan sub-folder.
            tornado.ioloop.IOLoop.instance().add_callback(self.add_thumbnail,current_metadata)

        return ret, current_metadata, errorMessage


    def delete_metadata(self, current_metadata=None):
        # [TODO]: 
        #   crose pool delete.
        # 

        ret = False

        if current_metadata is None:
            current_metadata = self.get_path()

        if not current_metadata is None:
            poolid = self.poolid
            db_path = current_metadata['path']
            if not self.poolid is None and not db_path is None:
                if current_metadata['type']=="file":
                    tornado.ioloop.IOLoop.instance().add_callback(self.delete_thumbnail,current_metadata)
                    ret = self.dbo_metadata.delete(poolid, db_path, self.account)
                else:
                    # recursively scan subfolder.
                    subfolders_dict = self.list_folder(poolid, db_path)
                    if not subfolders_dict is None:
                        if 'entries' in subfolders_dict:
                            for item in subfolders_dict['entries']:
                                self.delete_metadata(current_metadata=item)
                    # finally delete folder.
                    ret = self.dbo_metadata.delete(poolid, db_path, self.account)
        return ret

    
    def add_thumbnail(self, metadata):
        #[TOOD]
        # create thumbnail on server side.
        #[PS]: skip crose pool add.
        doc_id = metadata['id']
        dir_type = metadata['type']
        db_path = metadata['path']
        if doc_id > 0 and dir_type=="file":
            real_path = os.path.join(self.poolstorage, db_path[1:])
            thumbnail._generateThumbnails(real_path, doc_id)
        else:
            # recursively scan subfolder for copy API.
            # [PS]: skip crose pool copy in this case.
            subfolders_dict = self.list_folder(self.poolid, db_path)
            if not subfolders_dict is None:
                if 'entries' in subfolders_dict:
                    for item in subfolders_dict['entries']:
                        self.add_thumbnail(metadata=item)


    def delete_thumbnail(self, metadata):
        #[TOOD]
        # create thumbnail on server side.
        doc_id = metadata['id']
        dir_type = metadata['type']
        if doc_id > 0 and dir_type=="file":
            thumbnail._removeThumbnails(doc_id)
