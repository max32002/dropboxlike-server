#!/usr/bin/env python
#encoding=utf-8

import logging
from tornado.options import options
import os
import sys

from dbo.pool import DboPool
from controller.meta_manager import MetaManager

def travel(sql_client):
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

    #sys.exit()

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


