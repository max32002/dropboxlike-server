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
    def get_path( self, poolid, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE poolid=? AND path=? LIMIT 1'
        cursor = self.conn.execute(sql, (poolid, path,))
        out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 

    # get childes metadata..
    def get_contents( self, poolid, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE poolid=? and parent=?'
        cursor = self.conn.execute(sql, (poolid, path,))
        if not cursor is None:
            out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 

    # force create lost parent folders
    def check_and_create_parent(self, poolid, path, owner):
        out_dic = self.get_path(poolid, path)
        if len(out_dic) == 0:
            # current path not exist, create it.
            return self.create_folder(poolid, path, owner)

    def create_folder(self, poolid, path, owner):
        out_dic = {}
        out_dic['poolid'] = poolid
        out_dic['path'] = path
        out_dic['content_hash'] = ''
        out_dic['rev'] = ''
        out_dic['size'] = 0
        out_dic['client_modified'] = utils.get_timestamp()
        out_dic['lock'] = 0
        out_dic['is_dir'] = 1
        out_dic['editor'] = owner
        out_dic['owner'] = owner
        return self.insert(out_dic)

    def insert( self, in_dic ):
        out_dic = {}
        errorMessage = ""
        errorCode = 0
        ret = True

        if ret:
            for param in ['is_dir']:
                if in_dic[param] != 0 and in_dic[param] != 1:
                    errorMessage = param + ' value must be 0 or 1 for boolean in integer.'
                    errorCode = 1
                    ret = False

        if ret:
            for param in ['size']:
                if in_dic[param] == '':
                    errorMessage = param + ' value cannot be null.'
                    errorCode = 1
                    ret = False

        if ret:
            if in_dic.get('owner', '') == '':
                errorMessage = 'owner value cannot be empty.'
                errorCode = 1
                ret = False

        poolid = in_dic.get('poolid', 0)
        if poolid < 1 :
            errorMessage = 'poolid value wrong.'
            errorCode = 1
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

            try:
                sql = 'insert into metadata (poolid, path, content_hash, rev, size, is_dir, parent, name, client_modified, server_modified, editor, owner)'
                sql = sql + ' values(?,?,?,?,?,?,?,?,?,?,?,?) '
                #logging.info("sql: %s", sql)
                cursor = self.conn.execute(sql, (poolid,path,in_dic['content_hash'],in_dic['rev'],in_dic['size'],in_dic['is_dir'],parent_node, item_name,in_dic['client_modified'],utils.get_timestamp(),in_dic['editor'],in_dic['owner'],))
                self.conn.commit()

                if path != "" and cursor.lastrowid > 0:
                    self.dbo_delta.add_path(tag='folder',poolid=poolid,path=path,doc_id=cursor.lastrowid,account=in_dic['editor'])

                if self.last_transaction_path == path:
                    #logging.info("insert commit at path: {}".format(path))
                    out_dic['lastrowid'] = cursor.lastrowid
                    
            except sqlite3.IntegrityError:
                ret = False
                errorMessage = "insert metadata same path twice: {}".format(in_dic['path'].encode('utf-8').strip())
                errorCode = 2
                logging.error(errorMessage)
            except Exception as error:
                ret = False
                errorMessage = "insert metadata table Error: {}".format(error)
                errorCode = 3
                logging.error(errorMessage)

        return ret, out_dic, errorMessage, errorCode

    # PS: only update 'editor' field, keep 'owner' field no chaged.
    def update( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        error_flag = False

        poolid = ''
        if in_dic.get('poolid', 0) == 0:
            out_dic['error'] = 'poolid value cannot be empty.'
            error_flag = False
        else:
            poolid = in_dic['poolid']

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            error_flag = False
        else:
            path = in_dic['path']

        old_path = ''
        if in_dic.get('old_path', '') == '':
            out_dic['error'] = 'old_path value cannot be empty.'
            error_flag = False
        else:
            old_path = in_dic['old_path']

        if in_dic.get('editor', '') == '':
            out_dic['error'] = 'editor value cannot be empty.'
            error_flag = False

        if not error_flag:
            # get parent node by path
            #parent_node, item_name = self.get_parent_node(path)
            parent_node = ''
            item_name = ''
            if '/' in path:
                parent_node, item_name = os.path.split(path)
            else:
                item_name = path

            # skip parent's commit.
            if self.last_transaction_path is None:
                self.last_transaction_path = path

            if parent_node!='':
                self.check_and_create_parent(poolid, parent_node, in_dic['editor'])
            logging.info("update '%s' to metadata database ...", item_name)

            sql = 'update metadata set path = ?'
            if 'content_hash' in in_dic:
                sql += ' , content_hash = \'%s\'' % str(in_dic['content_hash']).replace("'", "''") 
            #[TODO]: Revision
            #sql += ' , rev = ?'
            if 'size' in in_dic:
                sql += ' , size = %d' % int(in_dic['size'])
            if 'mtime' in in_dic:
                sql += ' , mtime = \'%s\'' % str(in_dic['mtime']).replace("'", "''") 
            if 'is_dir' in in_dic:
                sql += ' , is_dir = %d' % int(in_dic['is_dir']) 
            sql += ' , parent=?, name = ? , modify_time = ?, editor = ? where poolid=? and path = ? '
            logging.info('update sql:%s' % (sql))
            self.conn.execute(sql, (path,parent_node, item_name, utils.get_timestamp(),in_dic['editor'], poolid, old_path,))
            
            # update child node path.
            #if out_dic['error'] == '':
            if old_path != path:
                # question: is need to update the account?
                sql = 'update metadata set path = ? || substr(path, length(?)+1) , parent = ? || substr(parent, length(?)+1), editor=? where path like ? '
                self.conn.execute(sql, (path,old_path,path,old_path,in_dic['editor'],old_path+'/%',))
                #self.conn.commit()

            # [TODO]: cross pool update.
            #

            self.conn.commit()
        else:
            logging.info("update metadata database error:%s.", out_dic['error'])
            return out_dic


    # PS: new 'owner' come from current editor.
    def copy( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        error_flag = False

        poolid = ''
        if in_dic.get('poolid', 0) == 0:
            out_dic['error'] = 'poolid value cannot be empty.'
            error_flag = False
        else:
            poolid = in_dic['poolid']

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            error_flag = False
        else:
            path = in_dic['path']

        old_path = ''
        if in_dic.get('old_path', '') == '':
            out_dic['error'] = 'old_path value cannot be empty.'
            error_flag = False
        else:
            old_path = in_dic['old_path']

        if in_dic.get('editor', '') == '':
            out_dic['error'] = 'editor value cannot be empty.'
            error_flag = False

        if not error_flag:
            # get parent node by path
            #parent_node, item_name = self.get_parent_node(path)
            parent_node = ''
            item_name = ''
            if '/' in path:
                parent_node, item_name = os.path.split(path)
            else:
                item_name = path

            # skip parent's commit.
            if self.last_transaction_path is None:
                self.last_transaction_path = path

            if parent_node!='':
                self.check_and_create_parent(poolid, parent_node, in_dic['editor'])
            logging.info("copy '%s' to metadata database ...", item_name)

            sql = "insert into metadata (poolid, path, comment, shared_flag, content_hash, rev, size, mtime, lock, is_dir, parent, name, thumbnail, modify_time, editor, owner) "
            sql += "select ?, 0, 0, content_hash, '', '', size, mtime, 0, is_dir, 0, ?, ?, thumbnail, modify_time,?,? from metadata where poolid=? and path=?"
            self.conn.execute(sql, (poolid, path,parent_node, item_name,in_dic['editor'],in_dic['editor'],poolid,old_path,))

            # copy child node path.
            #if out_dic['error'] == '':
            if old_path != path:
                sql = "insert into metadata (poolid, path, comment, shared_flag, content_hash, rev, size, mtime, lock, is_dir, parent, name, thumbnail, modify_time, editor, owner) "
                sql += "select ? || substr(path, length(?)+1), 0, 0, content_hash, '', '', size, mtime, 0, is_dir, ? || substr(parent, length(?)+1), name, thumbnail, modify_time,?,? from metadata where poolid=? and path like ?"
                self.conn.execute(sql, (poolid, path,old_path,path,old_path,in_dic['editor'],in_dic['editor'], poolid, old_path+'/%',))
                #self.conn.commit()

            # [TODO]: cross pool copy.
            #

            self.conn.commit()
        else:
            logging.info("copy metadata database error:%s.", out_dic['error'])
            return out_dic

    def delete( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''

        poolid = ''
        if in_dic.get('poolid', 0) == 0:
            out_dic['error'] = 'poolid value cannot be empty.'
            error_flag = False
        else:
            poolid = in_dic['poolid']

        path = ''
        if in_dic['path'] == '':
            out_dic['error'] = 'path value cannot be empty.'
            return out_dic
        else:
            path = in_dic['path']

        # [TODO]: cross pool copy.
        #


        if path != "/":
            self.conn.execute('delete from metadata where poolid, path = ? ', (path,))
        self.conn.execute('delete from metadata where poolid, path like ?', (path + '/%',))
        self.conn.commit()


    # get node id,
    #   node not exist, return -1,
    #   root always return 0.
    #   PS: not use to now...
    def get_parent_node(self, poolid, path):
        item_name = ''
        parent_path = ''
        parent_node = 0
        if '/' in path:
            parent_path, item_name = os.path.split(path)
            parent_node = self.search_parent_node(poolid, parent_path)
        else:
            item_name = path
        return parent_node, item_name

    # get node id,
    #   node not exist, return -1,
    #   root always return 0.
    #   PS: not use to now...
    def search_parent_node( self, poolid, path ):
        out_dic = {}
        out_dic['error'] = ''
        out_dic['n'] = 0
        out_dic['value'] = -1

        if path == '':
            # for root.
            out_dic['value'] = 0
            out_dic['n'] = 1
        else:
            # for not root
            lastChar = path[-1]
            if lastChar == '/':
                path = path[:-1]

            query_id = {}
            query_id['field_name'] = 'id'
            query_id['table_name'] = 'metadata'
            query_id['where_field'] = 'path'
            query_id['where_value'] = path

            # query db.
            out_dic = self.query_field(query_id)

            #print 'error:', out_dic['error']
            #print 'node count:', out_dic['n']

        #print 'node id:', out_dic['value']
        return_value = -1
        if out_dic['n'] > 0:
            return_value = out_dic['value']
        return return_value

    def query_field( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        out_dic['n'] = 0
        out_dic['value'] = ''

        order_by_string = ''
        if in_dic.get('order_by', '') != '':
            order_by_string = ' order by ' + in_dic['order_by']

        if in_dic.get('field_name', '') == '':
            out_dic['error'] = 'field_name value cannot be empty.'
            return out_dic

        if in_dic.get('table_name', '') == '':
            out_dic['error'] = 'table_name value cannot be empty.'
            return out_dic

        if in_dic.get('where_field', '') == '':
            out_dic['error'] = 'where_field value cannot be empty.'
            return out_dic

        if in_dic.get('where_value', '') == '':
            out_dic['error'] = 'where_value value cannot be empty.'
            return out_dic

        try:
            cursor = self.execute('select '+ in_dic['field_name'] +' from '+ in_dic['table_name'] +' where '+ in_dic['where_field'] +' = ? limit 1', (in_dic['where_value'],) )
            row = cursor.fetchone()
            out_dic['value'] = row[0]
            out_dic['n'] = 1

        except Exception as e:
            out_dic['error'] = 'fail to query record in a batch:' + e.args[0]
        finally:
            #db.close()
            return out_dic


    def list_one( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        out_dic['id'] = ''
        out_dic['path'] = ''
        out_dic['comment'] = ''
        out_dic['shared_flag'] = ''
        out_dic['content_hash'] = ''
        out_dic['rev'] = ''
        out_dic['size'] = ''
        out_dic['mtime'] = ''
        out_dic['lock'] = ''
        out_dic['is_dir'] = ''
        out_dic['name'] = ''

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            return out_dic
        else:
            path = in_dic['path']

        try:
            cursor = self.execute(' select path, comment, shared_flag, content_hash, permission, rev, modified, size, mtime, lock, is_dir, name, modify_time from local_metadata where path=? limit 1', (in_dic['path'],))
            row = cursor.fetchone()

            out_dic['path']         = row[0]
            out_dic['comment']      = row[1]
            out_dic['shared_flag']  = row[2]
            out_dic['content_hash']         = row[3]
            out_dic['permission']   = row[4]
            out_dic['rev']          = row[5]
            out_dic['thumb_exists'] = row[6]
            out_dic['modified']     = row[7]
            out_dic['size']        = row[8]
            out_dic['mtime']        = row[9]
            out_dic['lock']         = row[10]
            out_dic['is_dir']       = row[11]
            out_dic['name']         = row[12]
            out_dic['modify_time']  = row[13]

        except Exception as e:
            out_dic['error'] = 'fail to query record:' + e.args[0]
        finally:
            db.close()
            return out_dic


    def list( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        out_dic['n'] = 0

        order_by_string = ''
        if in_dic.get('order_by', '') != '':
            order_by_string = ' order by ' + in_dic['order_by']

        limit_string = ''
        if in_dic.get('limit', 0) > 0:
            limit_string = ' limit ' + str(in_dic['limit'])

        offset_string = ''
        if in_dic.get('offset', 0) > 0:
            offset_string = ' offset ' + str(in_dic['offset'])

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            return out_dic
        else:
            path = in_dic['path']

        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()
            cursor.execute( ' select path, comment, shared_flag, content_hash, permission, rev, thumb_exists, modified, size, mtime, lock, is_dir, name, modify_time from local_metadata where path like ?  or path = ?' + order_by_string + limit_string, (in_dic['path'] + '/%',in_dic['path'],) )
            #all_rows = cursor.fetchall()
            n = 0
            out_list = []
            #for row in all_rows:
            for row in cursor:
                sub_dic = {'path':row[0], 'comment':row[1], 'shared_flag':row[2], 'content_hash':row[3], 'permission':row[4], 'rev':row[5], 'thumb_exists':row[6], 'modified':row[7], 'size':row[8], 'mtime':row[9], 'lock':row[10], 'is_dir':row[11], 'name':row[12], 'modify_time':row[13]}
                out_list.append(sub_dic)
                n = n + 1
            out_dic['list'] = out_list
            out_dic['n'] = n
        except Exception as e:
            out_dic['error'] = 'fail to query record in a batch:' + e.args[0]
        finally:
            db.close()
            return out_dic

    # for list one level.
    def list_contents( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        out_dic['n'] = 0

        order_by_string = ''
        if in_dic.get('order_by', '') != '':
            order_by_string = ' order by ' + in_dic['order_by']

        limit_string = ''
        if in_dic.get('limit', 0) > 0:
            limit_string = ' limit ' + str(in_dic['limit'])

        offset_string = ''
        if in_dic.get('offset', 0) > 0:
            offset_string = ' offset ' + str(in_dic['offset'])

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            return out_dic
        else:
            path = in_dic['path']

        #path
        parent_node = self.search_parent_node(path)

        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()
            cursor.execute( ' select path, comment, shared_flag, content_hash, permission, rev, thumb_exists, modified, size, mtime, lock, is_dir, name, modify_time from local_metadata where parent = ?' + order_by_string + limit_string + offset_string, (parent_node,) )
            #all_rows = cursor.fetchall()
            n = 0
            out_list = []
            #for row in all_rows:
            for row in cursor:
                sub_dic = {'path':row[0], 'comment':row[1], 'shared_flag':row[2], 'content_hash':row[3], 'permission':row[4], 'rev':row[5], 'thumb_exists':row[6], 'modified':row[7], 'size':row[8], 'mtime':row[9], 'lock':row[10], 'is_dir':row[11], 'name':row[12], 'modify_time':row[13]}
                out_list.append(sub_dic)
                n = n + 1
            out_dic['list'] = out_list
            out_dic['n'] = n
        except Exception as e:
            out_dic['error'] = 'fail to query record in a batch:' + e.args[0]
        finally:
            db.close()
            return out_dic
