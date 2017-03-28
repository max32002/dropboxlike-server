#!/usr/bin/env python
#encoding=utf-8
from tornado.options import options
import tornado.ioloop
from tornado import gen
import logging
from app.dbo.metadata import DboMetadata
from app.dbo.pool import DboPoolSubscriber
from app.dbo.pool import DboPool
from app.dbo import dbconst
from app.lib import utils
from app.lib import thumbnail
import json
import sqlite3
import os

class MetaManager():
    dbo_metadata = None
    dbo_pool_subscriber = None
    account = None
    poolstorage = None
    poolid = None
    poolname = None
    can_edit = False
    query_path = None
    real_path = None
    full_path = ""
    db_path = None
    sys_sql_client = None

    def __init__(self, sql_client, current_user, query_path, check_shared_pool=True):
        self.sys_sql_client = sql_client
        self.dbo_pool_subscriber = DboPoolSubscriber(self.sys_sql_client)
        self.init_with_path(current_user, query_path, check_shared_pool)

    # get poolid by query_path
    # PS: set check_shared_pool=False to input db_path
    def init_with_path(self, current_user, query_path, check_shared_pool=True):
        ret = True

        self.account = current_user['account']
        self.poolid = current_user['poolid']

        self.poolname = None
        self.can_edit = False
        self.query_path = query_path
        if not self.poolid is None:
            # default access user-home.
            self.poolname = ""
            self.can_edit = True


        pool_dict = None
        if len(query_path) > 1:
            # query share_folder
            pool_dict = self.dbo_pool_subscriber.find_share_poolid(self.account, query_path)

        if check_shared_pool:
            if not pool_dict is None:
                self.poolid = pool_dict['poolid']
                self.poolname = pool_dict['poolname']
                # share folder under repo co-owner.
                self.can_edit = False
                if pool_dict['can_edit'] == 1:
                    self.can_edit = True

            # convert query_path to db_path
            if not self.poolid is None and not self.poolname is None:
                self.db_path = query_path
                if len(query_path) > 0:
                    self.db_path = query_path[len(self.poolname):]
        else:
            # convert query_path to db_path
            self.db_path = query_path

            if not pool_dict is None:
                #cross pool...
                ret = False

        self.poolstorage = None
        self.real_path = None
        self.full_path = query_path
        if not self.poolid is None:
            self.poolstorage = u'%s/storagepool/%s' % (options.storage_access_point, self.poolid)
            #logging.info('options.storage_access_point %s' % (options.storage_access_point))
            #logging.info('poolstorage %s' % (self.poolstorage))
            if self.dbo_metadata is None:
                #print "open metadata at pool: %d" % (self.poolid,)
                metadata_conn = self.open_metadata_db(self.poolid)
                self.dbo_metadata = DboMetadata(metadata_conn)

            db_path_for_join = ""
            self.real_path = self.poolstorage
            if len(self.db_path) > 0:
                db_path_for_join = self.db_path[1:]
                #print "db_path_for_join", db_path_for_join
                #self.real_path = os.path.join(self.poolstorage, db_path_for_join.decode('utf-8'))
                self.real_path = os.path.join(self.poolstorage, db_path_for_join)
            #logging.info(u'user query metadata path:%s, at real path: %s' % (query_path, self.real_path))

            root_path = self.poolname
            #logging.info('db_path_for_join %s' % (db_path_for_join))
            self.full_path = root_path
            if len(db_path_for_join) > 0:
                self.full_path = u'%s/%s' % (root_path, db_path_for_join)
            #logging.info('full_path %s' % (self.full_path))

        return ret

    def contain_pool_array(self, query_path=None):
        if query_path is None:
            query_path = self.full_path
        #logging.info('query_path %s' % (query_path))
        return self.dbo_pool_subscriber.contain_share_poolid(self.account, query_path)

    def pool_owner(self, query_path=None):
        if query_path is None:
            query_path = self.full_path
        #logging.info('query_path %s' % (query_path))
        owner = self.account

        if not self.poolid is None:
            if len(query_path) > 1:
                dbo_pool = DboPool(self.sys_sql_client)
                pool_dict = dbo_pool.pk_query(self.poolid)
                if not pool_dict is None:
                    owner = pool_dict['ownerid']
        return owner

    # open database.
    #[TODO] multi-database solution.
    #def open_metadata(self, poolid):
    def get_metadata_db_path(self, poolid):
        db_path = u'%s/metadata.db' % (options.storage_access_point)
        #logging.info("open metadata poolid: %s ... ", db_path)
        return db_path


    # open database.
    #[TODO] multi-database solution.
    #def open_metadata(self, poolid):
    def open_metadata_db(self, poolid):
        #if not poolid is None:
            #db_path = '%s/metadata/%s/metadata.db' % (options.storage_access_point,poolid)
            #logging.info("owner metadata poolid: %s ... ", db_path)
            #client = sqlite3.connect(db_path)
        db_path = self.get_metadata_db_path(poolid)
        client = sqlite3.connect(db_path)
        return client



    # get current path metadata.
    def get_path(self, poolid=None, db_path=None):
        if poolid is None:
            poolid = self.poolid
        if db_path is None:
            db_path = self.db_path

        current_metadata = None
        if not poolid is None:
            if not self.dbo_metadata is None:
                current_metadata = self.dbo_metadata.get_metadata(poolid, db_path)
        if not current_metadata is None:
            current_metadata = self.convert_for_dropboxlike_dict(current_metadata)
        return current_metadata

    # get current folder metadata
    def list_folder(self, poolid=None, db_path=None, show_share_folder=False):
        if poolid is None:
            poolid = self.poolid
        if db_path is None:
            db_path = self.db_path
        if db_path is None:
            # unable found this path in database.
            db_path = self.query_path


        dic_children = None
        if not poolid is None:
            if not self.dbo_metadata is None:
                dic_children = self.dbo_metadata.list_folder(poolid, db_path)

        metadata_dic = {}
        contents = []

        # for small case used, use append for each item.
        if not dic_children is None:
            for item in dic_children:
                contents.append(self.convert_for_dropboxlike_dict(item))

        # add shared folder
        if show_share_folder and (self.poolname == "" or self.poolname is None):
            share_folder_array = self.dbo_pool_subscriber.list_share_poolid(self.account, db_path)
            for pool_dict in share_folder_array:
                doc_id = 0
                new_poolid = pool_dict['poolid']
                metadata_conn = self.open_metadata_db(new_poolid)
                dbo_share_folder_metadata = DboMetadata(metadata_conn)
                if not dbo_share_folder_metadata is None:
                    current_metadata = dbo_share_folder_metadata.get_metadata(new_poolid, "")
                    if not current_metadata is None:
                        doc_id = current_metadata['doc_id']
                
                share_folder_dict = {}
                share_folder_dict['id'] = doc_id
                share_folder_dict['path'] = pool_dict['poolname']
                parent_node, item_name = os.path.split(pool_dict['poolname'])
                share_folder_dict['name'] = item_name

                #out_dic['permission'] = "{"write": True}"ll
                share_folder_dict['permission'] = 'r'
                if pool_dict['can_edit'] == 1:
                    share_folder_dict['permission'] = 'rw'
                if pool_dict['status'] == dbconst.POOL_STATUS_SHARED:
                    share_folder_dict['permission'] = 'rwx'
                share_folder_dict['type'] = "folder"

                share_folder_dict['shared_folder'] = True
                contents.append(share_folder_dict)


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
            ret = self.delete_metadata(current_metadata=check_metadata)

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
    
    #@gen.coroutine
    def add_thumbnail(self, metadata):
        #yield gen.moment
        #[TOOD]
        # create thumbnail on server side.
        #[PS]: skip crose pool add.
        doc_id = metadata['id']
        dir_type = metadata['type']
        db_path = metadata['path']
        if doc_id > 0 and dir_type=="file":
            real_path = os.path.join(self.poolstorage, db_path[1:])
            #logging.info(u"add thumbnal for file: %s", real_path)
            thumbnail._generateThumbnails(real_path, doc_id)
        else:
            # recursively scan subfolder for copy API.
            # [PS]: skip crose pool copy in this case.
            subfolders_dict = self.list_folder(self.poolid, db_path)
            if not subfolders_dict is None:
                if 'entries' in subfolders_dict:
                    for item in subfolders_dict['entries']:
                        #print "add thumbnal for item:", item
                        #tornado.ioloop.IOLoop.current().spawn_callback(self.add_thumbnail,item)
                        self.add_thumbnail(metadata=item)

    def delete_thumbnail(self, metadata):
        #[TOOD]
        # create thumbnail on server side.
        doc_id = metadata['id']
        dir_type = metadata['type']
        if doc_id > 0 and dir_type=="file":
            thumbnail._removeThumbnails(doc_id)

    def count_usage(self, poolid=None):
        if poolid is None:
            poolid = self.poolid
        return self.dbo_metadata.get_space_usage(poolid)


    def _getMtimeFromFile(self, real_path):
        client_modified = 0
        if os.path.isfile(real_path):
            try:
                client_modified = os.path.getmtime(real_path)
            except OSError:
                client_modified = 0
        return client_modified

    def add_metadata_from_file(self, skip_content_hash_check=False):
        # only user misc at here.
        from app.lib import misc

        is_pass_check = False
        query_result = None
        errorMessage = ""

        real_path = self.real_path
        #print "real_path:", real_path
        #logging.info("start to check file:" + real_path)
        if os.path.isfile(real_path):
            # TODO: reversion control.
            rev=None

            check_metadata = self.get_path()
            if check_metadata is None:
                client_modified = self._getMtimeFromFile(real_path)
                size=os.stat(real_path).st_size
                content_hash=misc.md5_file(real_path)
                is_pass_check, query_result, errorMessage = self.add_metadata(size=size, content_hash=content_hash, client_modified=client_modified)
            else:
                client_modified = self._getMtimeFromFile(real_path)
                size=os.stat(real_path).st_size
                content_hash = None

                is_need_to_update = False
                if not is_need_to_update:
                    if long(size) != long(check_metadata['size']):
                        is_need_to_update = True
                if not is_need_to_update:
                    if long(client_modified) != long(check_metadata['client_modified']):
                        is_need_to_update = True

                if not is_need_to_update:
                    if not skip_content_hash_check:
                        content_hash=misc.md5_file(real_path)
                        if content_hash != check_metadata['content_hash']:
                            is_need_to_update = True

                if is_need_to_update:
                    if content_hash is None:
                        content_hash=misc.md5_file(real_path)
                    is_pass_check, query_result, errorMessage = self.move_metadata(self.poolid, self.db_path, size=size, content_hash=content_hash, client_modified=client_modified)
                else:
                    # the same, skip update
                    pass
        else:
            errorMessage = "file not exist on server"

        return is_pass_check, query_result, errorMessage

