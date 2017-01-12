
import logging
from dbo.basetable import BaseTable
from lib import utils
import os
import sqlite3

#############################################################
class DboMetadata(BaseTable):
    sql_return_fields = "doc_id,path,comment,shared_flag,hash,permission,rev,bytes,mtime,lock,is_dir,favorite,parent,name,thumbnail,modify_time,editor,owner"
    sql_table_name = "metadata"
    sql_primary_key = "path"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `metadata` (
    `doc_id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `path`  varchar NOT NULL,
    `comment`   integer,
    `shared_flag`   integer NOT NULL,
    `hash`  varchar,
    `permission`    varchar,
    `rev`   varchar,
    `bytes` integer NOT NULL,
    `mtime` varchar,
    `lock`  integer NOT NULL,
    `is_dir`    integer NOT NULL,
    `favorite`    integer NOT NULL,
    `parent`    varchar NOT NULL,
    `name`  varchar NOT NULL,
    `thumbnail` integer,
    `modify_time`   integer,
    `editor`   TEXT NOT NULL,
    `owner`   TEXT NOT NULL
);
    '''
    sql_create_index = ['CREATE UNIQUE INDEX IF NOT EXISTS metadata_path ON metadata(path);',
    'CREATE INDEX IF NOT EXISTS metadata_parent ON metadata(parent);',
    'CREATE INDEX IF NOT EXISTS metadata_thumbnail ON metadata(thumbnail);'
    ]
    last_transaction_path = None

    # get current path metadata.
    def get_path( self, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE path=? LIMIT 1'
        cursor = self.conn.execute(sql, (path,))
        out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 

    # get childes metadata..
    def get_contents( self, path):
        out_dic = None
        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE parent=?'
        cursor = self.conn.execute(sql, (path,))
        if not cursor is None:
            out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 

    # force create lost parent folders
    def check_and_create_parent(self, path, owner):
        if len(path) > 0:
            out_dic = self.get_path(path)
            if len(out_dic) == 0:
                # current path not exist, create it.
                self.create_folder(path, owner)
                parent_node, item_name = os.path.split(path)
                self.check_and_create_parent(parent_node, owner)
            else:
                # path exist
                pass

    def create_folder(self, path, owner):
        out_dic = {}
        out_dic['path'] = path
        out_dic['comment'] = 0
        out_dic['shared_flag'] = 0
        out_dic['hash'] = ''
        out_dic['permission'] = ''
        out_dic['rev'] = ''
        out_dic['bytes'] = 0
        out_dic['mtime'] = ''
        out_dic['lock'] = 0
        out_dic['is_dir'] = 1
        out_dic['favorite'] = 0
        out_dic['editor'] = owner
        out_dic['owner'] = owner
        self.insert(out_dic)

    def insert( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        error_flag = False

        for param in ['shared_flag', 'lock', 'is_dir','favorite']:
            if in_dic[param] != 0 and in_dic[param] != 1:
                out_dic['error'] = param + ' value must be 0 or 1 for boolean in integer.'
                error_flag = False

        for param in ['bytes']:
            if in_dic[param] == '':
                out_dic['error'] = param + ' value cannot be null.'
                error_flag = False

        path = ''
        if in_dic.get('path', '') == '':
            out_dic['error'] = 'path value cannot be empty.'
            error_flag = False
        else:

            path = in_dic['path']

        if in_dic.get('owner', '') == '':
            out_dic['error'] = 'owner value cannot be empty.'
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
                self.check_and_create_parent(parent_node, in_dic['owner'])
            logging.info("insert '%s' to metadata database ...", item_name)

            try:
                sql = 'insert into metadata (path, comment, shared_flag, hash, permission, rev, bytes, mtime, lock, is_dir, favorite, parent, name, modify_time, editor, owner) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '
                cursor = self.conn.execute(sql, (in_dic['path'],in_dic['comment'],in_dic['shared_flag'],in_dic['hash'],in_dic['permission'],in_dic['rev'],in_dic['bytes'],in_dic['mtime'],in_dic['lock'],in_dic['is_dir'],in_dic['favorite'],parent_node, item_name,utils.get_docid(),in_dic['owner'],in_dic['owner'],))
                self.conn.commit()
                if self.last_transaction_path == path:
                    #logging.info("insert commit at path: {}".format(path))
                    out_dic['lastrowid'] = cursor.lastrowid
                    
            except sqlite3.IntegrityError:
                logging.info("insert metadata same path twice: {}".format(in_dic['path']))
            except Exception as error:
                logging.info("insert metadata table Error: {}".format(error))
                pass

        else:
            logging.info("inser metadata database error:%s.", out_dic['error'])
            return out_dic

    # PS: only update 'editor' field, keep 'owner' field no chaged.
    def update( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        error_flag = False

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
                self.check_and_create_parent(parent_node, in_dic['editor'])
            logging.info("update '%s' to metadata database ...", item_name)

            sql = 'update metadata set path = ?'
            if 'comment' in in_dic:
                sql += ' , comment = %d' % int(in_dic['comment'])
            if 'shared_flag' in in_dic:
                sql += ' , shared_flag = %d' % int(in_dic['shared_flag']) 
            if 'hash' in in_dic:
                sql += ' , hash = \'%s\'' % str(in_dic['hash']).replace("'", "''") 
            #sql += ' , permission = ?'
            #sql += ' , rev = ?'
            if 'bytes' in in_dic:
                sql += ' , bytes = %d' % int(in_dic['bytes'])
            if 'mtime' in in_dic:
                sql += ' , mtime = \'%s\'' % str(in_dic['mtime']).replace("'", "''") 
            if 'lock' in in_dic:
                sql += ' , lock = %d' % int(in_dic['lock']) 
            if 'is_dir' in in_dic:
                sql += ' , is_dir = %d' % int(in_dic['is_dir']) 
            if 'favorite' in in_dic:
                sql += ' , favorite = %d' % int(in_dic['favorite']) 
            if 'thumbnail' in in_dic:
                sql += ' , thumbnail = %d' % int(in_dic['thumbnail']) 
            sql += ' , parent=?, name = ? , modify_time = ?, editor = ? where path = ? '
            logging.info('update sql:%s' % (sql))
            self.conn.execute(sql, (path,parent_node, item_name, utils.get_timestamp(),in_dic['editor'],old_path,))
            
            # update child node path.
            #if out_dic['error'] == '':
            if old_path != path:
                # question: is need to update the account?
                sql = 'update metadata set path = ? || substr(path, length(?)+1) , parent = ? || substr(parent, length(?)+1), editor=? where path like ? '
                self.conn.execute(sql, (path,old_path,path,old_path,in_dic['editor'],old_path+'/%',))
                #self.conn.commit()

            self.conn.commit()
        else:
            logging.info("update metadata database error:%s.", out_dic['error'])
            return out_dic


    # PS: new 'owner' come from current editor.
    def copy( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''
        error_flag = False

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
                self.check_and_create_parent(parent_node, in_dic['editor'])
            logging.info("copy '%s' to metadata database ...", item_name)

            sql = "insert into metadata (path, comment, shared_flag, hash, permission, rev, bytes, mtime, lock, is_dir, favorite, parent, name, thumbnail, modify_time, editor, owner) "
            sql += "select ?, 0, 0, hash, '', '', bytes, mtime, 0, is_dir, 0, ?, ?, thumbnail, modify_time,?,? from metadata where path=?"
            self.conn.execute(sql, (path,parent_node, item_name,in_dic['editor'],in_dic['editor'],old_path,))

            # copy child node path.
            #if out_dic['error'] == '':
            if old_path != path:
                sql = "insert into metadata (path, comment, shared_flag, hash, permission, rev, bytes, mtime, lock, is_dir, favorite, parent, name, thumbnail, modify_time, editor, owner) "
                sql += "select ? || substr(path, length(?)+1), 0, 0, hash, '', '', bytes, mtime, 0, is_dir, favorite, ? || substr(parent, length(?)+1), name, thumbnail, modify_time,?,? from metadata where path like ?"
                self.conn.execute(sql, (path,old_path,path,old_path,in_dic['editor'],in_dic['editor'],old_path+'/%',))
                #self.conn.commit()

            self.conn.commit()
        else:
            logging.info("copy metadata database error:%s.", out_dic['error'])
            return out_dic

    def delete( self, in_dic ):
        out_dic = {}
        out_dic['error'] = ''

        if in_dic['path'] == '':
            out_dic['error'] = 'key value cannot be empty.'
            return out_dic

        self.conn.execute('delete from metadata where path = ? ', (in_dic['path'],))
        self.conn.execute('delete from metadata where path like ?', (in_dic['path'] + '/%',))
        self.conn.commit()


    # get node id,
    #   node not exist, return -1,
    #   root always return 0.
    #   PS: not use to now...
    def get_parent_node(self, path):
        item_name = ''
        parent_path = ''
        parent_node = 0
        if '/' in path:
            parent_path, item_name = os.path.split(path)
            parent_node = self.search_parent_node(parent_path)
        else:
            item_name = path
        return parent_node, item_name

    # get node id,
    #   node not exist, return -1,
    #   root always return 0.
    #   PS: not use to now...
    def search_parent_node( self, path ):
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

            # for level 0+.
            #if path == '':
                #path = "/"
            #print 'real query path:'+ path

            # for level 1+.
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

    #   PS: not use to now...
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
        out_dic['hash'] = ''
        out_dic['permission'] = ''
        out_dic['rev'] = ''
        out_dic['bytes'] = ''
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
            cursor = self.execute(' select path, comment, shared_flag, hash, permission, rev, modified, bytes, mtime, lock, is_dir, name, modify_time from local_metadata where path=? limit 1', (in_dic['path'],))
            row = cursor.fetchone()

            out_dic['path']         = row[0]
            out_dic['comment']      = row[1]
            out_dic['shared_flag']  = row[2]
            out_dic['hash']         = row[3]
            out_dic['permission']   = row[4]
            out_dic['rev']          = row[5]
            out_dic['thumb_exists'] = row[6]
            out_dic['modified']     = row[7]
            out_dic['bytes']        = row[8]
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
            cursor.execute( ' select path, comment, shared_flag, hash, permission, rev, thumb_exists, modified, bytes, mtime, lock, is_dir, name, modify_time from local_metadata where path like ?  or path = ?' + order_by_string + limit_string, (in_dic['path'] + '/%',in_dic['path'],) )
            #all_rows = cursor.fetchall()
            n = 0
            out_list = []
            #for row in all_rows:
            for row in cursor:
                sub_dic = {'path':row[0], 'comment':row[1], 'shared_flag':row[2], 'hash':row[3], 'permission':row[4], 'rev':row[5], 'thumb_exists':row[6], 'modified':row[7], 'bytes':row[8], 'mtime':row[9], 'lock':row[10], 'is_dir':row[11], 'name':row[12], 'modify_time':row[13]}
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
            cursor.execute( ' select path, comment, shared_flag, hash, permission, rev, thumb_exists, modified, bytes, mtime, lock, is_dir, name, modify_time from local_metadata where parent = ?' + order_by_string + limit_string + offset_string, (parent_node,) )
            #all_rows = cursor.fetchall()
            n = 0
            out_list = []
            #for row in all_rows:
            for row in cursor:
                sub_dic = {'path':row[0], 'comment':row[1], 'shared_flag':row[2], 'hash':row[3], 'permission':row[4], 'rev':row[5], 'thumb_exists':row[6], 'modified':row[7], 'bytes':row[8], 'mtime':row[9], 'lock':row[10], 'is_dir':row[11], 'name':row[12], 'modify_time':row[13]}
                out_list.append(sub_dic)
                n = n + 1
            out_dic['list'] = out_list
            out_dic['n'] = n
        except Exception as e:
            out_dic['error'] = 'fail to query record in a batch:' + e.args[0]
        finally:
            db.close()
            return out_dic
