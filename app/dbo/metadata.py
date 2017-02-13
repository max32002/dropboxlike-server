#!/usr/bin/env python
#encoding=utf-8
import logging
from app.dbo.basetable import BaseTable
from app.dbo.delta import DboDelta
from app.lib import utils
import os
import sqlite3

#############################################################
class DboMetadata(BaseTable):
    sql_return_fields = "doc_id,poolid,path,content_hash,rev,size,is_dir,parent,name,client_modified,server_modified,editor,owner"
    sql_table_name = "metadata"
    sql_primary_key = "path"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `metadata` (
    `doc_id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `poolid`  integer NOT NULL,
    `path`  varchar NOT NULL,
    `content_hash`  varchar,
    `rev`   varchar,
    `size` integer NOT NULL,
    `is_dir`    integer NOT NULL,
    `parent`    varchar,
    `name`  varchar NOT NULL,
    `client_modified` integer,
    `server_modified` integer NOT NULL,
    `editor`   TEXT NOT NULL,
    `owner`   TEXT NOT NULL
);
    '''
    sql_create_index = ['CREATE UNIQUE INDEX IF NOT EXISTS metadata_path ON metadata(poolid,path);',
    'CREATE INDEX IF NOT EXISTS metadata_parent ON metadata(poolid,parent);',
    ]
    last_transaction_path = None

    dbo_delta = None

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)
        self.dbo_delta = DboDelta(db_conn)

    # get current path metadata.
    def get_metadata( self, poolid, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE poolid=? AND path=? LIMIT 1'
        #print "sql:",sql, poolid, path
        cursor = self.conn.execute(sql, (poolid, path,))
        row_array = self.get_dict_by_cursor(cursor)
        if len(row_array) > 0:
            out_dic = row_array[0]
        #print "metadata dict:", out_dic
        return out_dic 

    # get childes metadata..
    def list_folder( self, poolid, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE poolid=? and parent=?'
        cursor = self.conn.execute(sql, (poolid, path,))
        if not cursor is None:
            out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 

    # force create lost parent folders
    def check_and_create_parent(self, poolid, path, owner):
        out_dic = self.get_metadata(poolid, path)
        if out_dic is None:
            # current path not exist, create it.
            return self.create_folder(poolid, path, owner)

    def create_folder(self, poolid, path, owner):
        out_dic = {}
        out_dic['poolid'] = poolid
        out_dic['path'] = path
        out_dic['content_hash'] = None
        out_dic['rev'] = None
        out_dic['size'] = 0
        out_dic['client_modified'] = utils.get_timestamp()
        out_dic['is_dir'] = 1
        out_dic['editor'] = owner
        out_dic['owner'] = owner
        return self.insert(out_dic)

    def insert( self, in_dic , autocommit=True):
        out_dic = {}
        errorMessage = ""
        ret = True

        if ret:
            for param in ['is_dir']:
                if in_dic[param] != 0 and in_dic[param] != 1:
                    errorMessage = param + ' value must be 0 or 1 for boolean in integer.'
                    ret = False

        if ret:
            for param in ['size']:
                if in_dic[param] == '':
                    errorMessage = param + ' value cannot be null.'
                    ret = False

        if ret:
            if in_dic.get('owner', '') == '':
                errorMessage = 'owner value cannot be empty.'
                ret = False

        poolid = in_dic.get('poolid', 0)
        if poolid < 1 :
            errorMessage = 'poolid value wrong.'
            ret = False

        path = in_dic.get('path', '')

        if ret:
            # get parent node by path
            parent_node = None
            item_name = path
            if len(path) > 0:
                parent_node, item_name = os.path.split(path)
                #print "parent_node, item_name:", parent_node, item_name

                # skip parent's commit.
                if self.last_transaction_path is None:
                    self.last_transaction_path = path

                if not parent_node is None:
                    if parent_node == "/":
                        parent_node = ""
                    #print "parent_node, check_and_create_parent:", parent_node
                    self.check_and_create_parent(poolid, parent_node, in_dic['owner'])

            #logging.info("start to insert '%s' to metadata database ...", item_name)

            current_metadata = None
            try:
                sql = 'insert into metadata (poolid, path, content_hash, rev, size, is_dir, parent, name, client_modified, server_modified, editor, owner)'
                sql = sql + ' values(?,?,?,?,?,?,?,?,?,?,?,?) '
                #logging.info("sql: %s", sql)
                cursor = self.conn.execute(sql, (poolid,path,in_dic['content_hash'],in_dic['rev'],in_dic['size'],in_dic['is_dir'],parent_node, item_name,in_dic['client_modified'],utils.get_timestamp(),in_dic['editor'],in_dic['owner'],))

                current_metadata = self.get_metadata(poolid, path)
                if not current_metadata is None:
                    self.add_metadata_to_delta(current_metadata, in_dic['editor'], autocommit=False)
                else:
                    ret = False
                    errorMessage = "data is lost after move metadata in database"

                if self.last_transaction_path != path:
                    #logging.info("insert commit at path: {}".format(path))
                    #out_dic['lastrowid'] = cursor.lastrowid
                    # force skip commit.
                    autocommit = False

                if autocommit:
                    self.conn.commit()
                    self.last_transaction_path = None

            except sqlite3.IntegrityError:
                ret = False
                errorMessage = "insert metadata same path twice: {}".format(in_dic['path'].encode('utf-8').strip())
                logging.error(errorMessage)
            except Exception as error:
                ret = False
                errorMessage = "insert metadata table Error: {}".format(error)
                logging.error(errorMessage)

        return ret, current_metadata, errorMessage

    # PS: only update 'editor' field, keep 'owner' field no chaged.
    def update( self, in_dic, autocommit=True):
        errorMessage = ""
        current_metadata = None
        ret = True

        poolid = ''
        if ret:
            if in_dic.get('poolid', 0) == 0:
                errorMessage = 'poolid value cannot be empty.'
                ret = False
            else:
                poolid = in_dic['poolid']

        path = ''
        if ret:
            if in_dic.get('path', '') == '':
                errorMessage = 'path value cannot be empty.'
                ret = False
            else:
                path = in_dic['path']

        old_poolid = ''
        if ret:
            if in_dic.get('old_poolid', '') == '':
                errorMessage = 'old_poolid value cannot be empty.'
                ret = False
            else:
                old_poolid = in_dic['old_poolid']

        old_path = ''
        if ret:
            if in_dic.get('old_path', '') == '':
                errorMessage = 'old_path value cannot be empty.'
                ret = False
            else:
                old_path = in_dic['old_path']

        if ret:
            if in_dic.get('editor', '') == '':
                errorMessage = 'editor value cannot be empty.'
                ret = False

        if ret:
            # get parent node by path
            parent_node, item_name = os.path.split(path)

            # skip parent's commit.
            if self.last_transaction_path is None:
                self.last_transaction_path = path

            if not parent_node is None:
                if parent_node == "/":
                    parent_node = ""
                self.check_and_create_parent(poolid, parent_node, in_dic['editor'])
            logging.info("update '%s' to metadata database ...", item_name)

            try:
                sql = 'update metadata set poolid=?, path = ?'
                if 'content_hash' in in_dic:
                    sql += ' , content_hash = \'%s\'' % str(in_dic['content_hash']).replace("'", "''") 
                #[TODO]: Revision
                #sql += ' , rev = ?'
                if 'size' in in_dic:
                    sql += ' , size = %d' % int(in_dic['size'])
                if 'client_modified' in in_dic:
                    sql += ' , client_modified = %d' % int(in_dic['client_modified'])
                if 'is_dir' in in_dic:
                    sql += ' , is_dir = %d' % int(in_dic['is_dir']) 
                sql += ' , parent=?, name = ? , server_modified = ?, editor = ? where poolid=? and path = ? '
                #logging.info('update sql:%s' % (sql))

                self.conn.execute(sql, (poolid,path,parent_node, item_name, utils.get_timestamp(),in_dic['editor'], old_poolid, old_path,))
                
                # update child node path.
                # question: is need to update the editor/owner account?
                if not(old_poolid==poolid and old_path==path):
                    # skip for file revision.
                    sql = 'update metadata set path = ? || substr(path, length(?)+1) , parent = ? || substr(parent, length(?)+1), editor=? where poolid=? and path like ? '
                    self.conn.execute(sql, (path, old_path, path, old_path, in_dic['editor'], old_poolid, old_path+'/%',))
                #self.conn.commit()

                current_metadata = self.get_metadata(poolid, path)
                if not current_metadata is None:
                    self.dbo_delta.delete_path(poolid=old_poolid,path=old_path,account=in_dic['editor'], autocommit=False)

                    self.add_metadata_to_delta(current_metadata, in_dic['editor'], autocommit=False)
                else:
                    ret = False
                    errorMessage = "data is lost after move metadata in database"

                # must commit at finish!
                if autocommit:
                    self.conn.commit()
                    self.last_transaction_path = None
            except Exception as error:
                ret = False
                errorMessage = "update metadata table Error: {}".format(error)
                logging.error(errorMessage)

        return ret, current_metadata, errorMessage

    def add_metadata_to_delta(self, current_metadata, account, autocommit=True):
        if not current_metadata is None:
            tag="file"
            if current_metadata['is_dir'] == 1:
                tag="folder"

            if current_metadata['path'] != "" and current_metadata['doc_id'] > 0:
                self.dbo_delta.add_path(tag=tag,poolid=current_metadata['poolid'],path=current_metadata['path'],doc_id=current_metadata['doc_id'],account=account, autocommit=autocommit)

            if tag=="folder":
                children_array = self.list_folder(current_metadata['poolid'],current_metadata['path'])
                for children_metadata in children_array:
                    self.add_metadata_to_delta(children_metadata, account, autocommit=autocommit)
   

    # PS: new 'owner' come from current editor.
    def copy( self, in_dic, autocommit=True):
        errorMessage = ""
        current_metadata = None
        ret = True

        poolid = ''
        if ret:
            if in_dic.get('poolid', 0) == 0:
                errorMessage = 'poolid value cannot be empty.'
                ret = False
            else:
                poolid = in_dic['poolid']

        path = ''
        if ret:
            if in_dic.get('path', '') == '':
                errorMessage = 'path value cannot be empty.'
                ret = False
            else:
                path = in_dic['path']

        old_poolid = ''
        if ret:
            if in_dic.get('old_poolid', '') == '':
                errorMessage = 'old_poolid value cannot be empty.'
                ret = False
            else:
                old_poolid = in_dic['old_poolid']

        old_path = ''
        if ret:
            if in_dic.get('old_path', '') == '':
                errorMessage = 'old_path value cannot be empty.'
                ret = False
            else:
                old_path = in_dic['old_path']

        if ret:
            if in_dic.get('editor', '') == '':
                errorMessage = 'editor value cannot be empty.'
                ret = False

        if ret:
            # get parent node by path
            parent_node, item_name = os.path.split(path)

            # skip parent's commit.
            if self.last_transaction_path is None:
                self.last_transaction_path = path

            if not parent_node is None:
                if parent_node == "/":
                    parent_node = ""
                self.check_and_create_parent(poolid, parent_node, in_dic['editor'])

            logging.info("copy '%s' to metadata database ...", item_name)

            try:
                #[TODO]: generate new rev for new file.

                sql = "insert into metadata (poolid, path, content_hash, rev, size, is_dir, parent, name, client_modified, server_modified, editor, owner) "
                sql += "select ?, ?, content_hash, null, size, is_dir, ?, ?, client_modified, ?, ?, owner from metadata where poolid=? and path=?"
                self.conn.execute(sql, (poolid, path, parent_node, item_name, utils.get_timestamp(), in_dic['editor'],old_poolid,old_path,))
                #logging.info("sql: %s", sql)

                # copy child node path.
                sql = "insert into metadata (poolid, path, content_hash, rev, size, is_dir, parent, name, client_modified, server_modified, editor, owner) "
                sql += "select ?, ? || substr(path, length(?)+1), content_hash, null, size, is_dir, ? || substr(parent, length(?)+1), name, client_modified, ?, ?, owner from metadata where poolid=? and path like ?"
                self.conn.execute(sql, (poolid, path, old_path, path, old_path, utils.get_timestamp(), in_dic['editor'], old_poolid, old_path+'/%',))
                #logging.info("sql: %s", sql)

                current_metadata = self.get_metadata(poolid, path)
                if not current_metadata is None:
                    self.add_metadata_to_delta(current_metadata, in_dic['editor'], autocommit=False)
                else:
                    ret = False
                    errorMessage = "data is lost after move metadata in database"

                # must commit at finish!
                if autocommit:
                    self.conn.commit()
                    self.last_transaction_path = None
            except Exception as error:
                ret = False
                errorMessage = "copy metadata table Error: {}".format(error)
                logging.error(errorMessage)

        return ret, current_metadata, errorMessage


    def delete( self, poolid, path, account, autocommit=True):
        errorMessage = ""
        ret = True

        if poolid < 1 :
            errorMessage = 'poolid value wrong.'
            ret = False

        if path is None:
            errorMessage = 'path value wrong.'
            ret = False

        if ret:
            try:
                self.conn.execute('delete from metadata where poolid=? and path = ? ', (poolid, path,))
                self.conn.execute('delete from metadata where poolid=? and path like ?', (poolid, path + '/%',))

                self.dbo_delta.delete_path(poolid=poolid,path=path,account=account,autocommit=False)

                if autocommit:
                    self.conn.commit()

            except Exception as error:
                ret = False
                errorMessage = "delete metadata table Error: {}".format(error)
                logging.error(errorMessage)

        return ret, errorMessage
