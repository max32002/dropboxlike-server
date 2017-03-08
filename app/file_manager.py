#!/usr/bin/env python
#encoding=utf-8

import logging
from tornado.options import options
import os
import sys

import sqlite3
from dbo.pool import DboPool
from dbo.metadata import DboMetadata
from controller.meta_manager import MetaManager

def travel(sql_client):
    travel_metadata(sql_client)
    travel_disk(sql_client)

def travel_metadata(sql_client):
    #print("start to travel.")
    dbo_pool = DboPool(sql_client)

    for pool in dbo_pool.all():
        poolid = pool['poolid']
        owner = pool['ownerid']
        current_user = {'account':owner, 'poolid': poolid}
        #print "current_user", current_user
        metadata_client = open_metadata_db(poolid)
        dbo_metadata = DboMetadata(metadata_client)

        metadata_manager = MetaManager(sql_client, current_user, "", check_shared_pool=False)
        for files_row in dbo_metadata.list_pool(poolid):
            path = files_row['path']
            #print "path", path
            metadata_manager.init_with_path(current_user,path,check_shared_pool=False)
            real_path = metadata_manager.real_path
            if not real_path is None:
                if not os.path.isfile(real_path):
                    #print "real_path not exist", real_path
                    metadata_manager.delete_metadata()

# open database.
#[TODO] multi-database solution.
#def open_metadata(self, poolid):
def open_metadata_db(poolid):
    #if not poolid is None:
        #db_path = '%s/metadata/%s/metadata.db' % (options.storage_access_point,poolid)
        #logging.info("owner metadata poolid: %s ... ", db_path)
        #client = sqlite3.connect(db_path)
    db_path = '%s/metadata.db' % (options.storage_access_point)
    #logging.info("open metadata poolid: %s ... ", db_path)
    client = sqlite3.connect(db_path)
    return client

def travel_disk(sql_client):
    #print("start to travel.")
    dbo_pool = DboPool(sql_client)

    for pool in dbo_pool.all():
        poolid = pool['poolid']
        owner = pool['ownerid']
        current_user = {'account':owner, 'poolid': poolid}
        metadata_manager = MetaManager(sql_client, current_user, "", check_shared_pool=False)
        #print "current_user", current_user
        poolstorage = u'%s/storagepool/%s' % (options.storage_access_point,poolid)
        #print "poolstorage", poolstorage
        list_files(poolstorage, metadata_manager, current_user)

def list_files(startpath, metadata_manager, current_user):
    #print "startpath:", os.path.abspath(startpath)
    for root, dirs, files in os.walk(startpath):
        #print "root:", os.path.abspath(root)
        #db_path = os.path.abspath(root)[len(os.path.abspath(startpath)):]
        db_path = root.replace(startpath, '')
        #print "db_path:", db_path
        #level = root.replace(startpath, '').count(os.sep)
        #indent = ' ' * 4 * (level)
        #print('{}{}/'.format(indent, os.path.basename(root)))
        #subindent = ' ' * 4 * (level + 1)
        files = [decodeName(f) for f in files]
        for f in files:
            #print "type" , type(db_path), type(f)
            file_db_path = u'{}/{}'.format(db_path, f)
            #print file_db_path
            metadata_manager.init_with_path(current_user,file_db_path,check_shared_pool=False)
            metadata_manager.add_metadata_from_file()

def decodeName(name):
    if type(name) == str: # leave unicode ones alone
        try:
            name = name.decode('utf8')
        except:
            name = name.decode('windows-1252')
    return name

if __name__ == "__main__":
    import settings
    import sqlite3
    settings.define_app_options()
    print("db path:", options.sys_db)
    sql_client = sqlite3.connect(options.sys_db)
    travel(sql_client)

