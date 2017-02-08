#!/usr/bin/env python
#encoding=utf-8
from tornado.options import options
import logging
from app.dbo.metadata import DboMetadata
from app.dbo.pool import DboPoolSubscriber
from app.lib import utils
import json
import sqlite3
import os

class MetaManager():
    '''!Metadata API Controller'''
    dbo_metadata = None
    account = None
    poolpath = None
    poolid = None
    poolname = None
    path = None
    real_path = None

    def __init__(self, sql_client, current_user, path):
        self.path = path
        self.account = current_user['account']
        self.poolid = current_user['poolid']
        if not self.poolid is None:
            # default access user-home.
            self.poolname = ""

        if len(path) > 1:
            # query share_folder
            pool_subscriber_dbo = DboPoolSubscriber(sql_client)
            db_poolid, db_poolname = pool_subscriber_dbo.find_share_poolid(self.account, path)
            if not db_poolid is None:
                self.poolid = db_poolid
                self.poolname = db_poolname

        if not self.poolid is None:
            self.poolpath = '%s/storagepool/%s' % (options.storage_access_point,self.poolid)
            #logging.info('options.storage_access_point %s' % (options.storage_access_point))
            #logging.info('poolpath %s' % (self.poolpath))
            metadata_conn = self.open_metadata_db(self.poolid)
            self.dbo_metadata = DboMetadata(metadata_conn)

            db_path = path
            if path != "":
                db_path = path[len(self.poolname):]
            self.real_path = os.path.join(self.poolpath, db_path[1:])
            logging.info('user query metadata path:%s, at real path: %s' % (path, self.real_path))

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


    def query_formated(self):
        metadata_dic = {}

        dic_children = self.dbo_metadata.get_contents(self.poolid, self.path)
        #print 'dic_children:%s' % (dic_children)
        contents = []

        # for small case used.
        for item in dic_children:
            contents.append(self.convert_for_dropboxlike_dict(item))
        metadata_dic['entries']=contents
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
        in_dic = {}
        in_dic['path'] = '/' + tmp_dict['path']
        in_dic['content_hash'] = tmp_dict['content_hash']
        #in_dic['permission'] = "{"write": True}"ll
        in_dic['permission'] = tmp_dict['permission']
        in_dic['rev'] = tmp_dict['rev']
        in_dic['size'] = tmp_dict['size']
        in_dic['is_dir'] = (True if tmp_dict['is_dir']==1 else False)
        in_dic['client_modified'] = tmp_dict['client_modified']
        in_dic['server_modified'] = tmp_dict['server_modified']
        return in_dic

    def add_metadata(self, path, size=0, rev='', client_modified=None, is_dir=0):
        in_dic = {}
        in_dic['poolid'] = self.poolid
        in_dic['path'] = path
        in_dic['content_hash'] = ''
        in_dic['rev'] = rev
        in_dic['size'] = size
        if client_modified is None:
            client_modified = utils.get_timestamp()
        in_dic['client_modified'] = client_modified
        in_dic['is_dir'] = is_dir
        in_dic['editor'] = self.account
        in_dic['owner'] = self.account
        return self.dbo_metadata.insert(in_dic)

    def move(self, from_path, to_path, rev=None, size=None, client_modified=None, is_dir=None):
        in_dic = {}
        in_dic['old_path'] = from_path
        in_dic['path'] = to_path
        #if not content_hash is None:
        #    in_dic['content_hash'] = '' 
        if not rev is None:
            in_dic['rev'] = rev 
        if not size is None:
            in_dic['size'] = size
        if not client_modified is None:
            in_dic['client_modified'] = client_modified 
        if not is_dir is None:
            in_dic['is_dir'] = is_dir
        in_dic['editor'] = self.account
        return self.dbo_metadata.update(in_dic)

    def copy(self, from_path, to_path):
        in_dic = {}
        in_dic['old_path'] = from_path
        in_dic['path'] = to_path
        in_dic['editor'] = self.account
        return self.dbo_metadata.copy(in_dic)


    def remove(self, path):
        # todo: 
        #   check permission...
        # 

        in_dic = {}
        in_dic['path'] = path
        return self.dbo_metadata.delete(in_dic)

