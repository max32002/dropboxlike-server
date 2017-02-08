#!/usr/bin/env python
#encoding=utf-8
import logging
from app.dbo.basetable import BaseTable
from app.lib import utils

#data object for Account
#############################################################
class DboDelta(BaseTable):
    sql_return_fields = "tag,poolid,path,doc_id,account,update_time"
    sql_table_name = "delta"
    sql_primary_key = "delta_id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `delta` (
    `delta_id`  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `poolid`  INTEGER NOT NULL,
    `tag`    TEXT NOT NULL,
    `doc_id`  INTEGER NOT NULL,
    `path`  TEXT NOT NULL,
    `account`   TEXT NOT NULL,
    `update_time` INTEGER NOT NULL
);
    '''
    sql_create_index = ['''
CREATE INDEX IF NOT EXISTS delta_timestamp ON delta(poolid,update_time);
    ''','''
CREATE INDEX IF NOT EXISTS delta_path ON delta(poolid,path);
    ''']

    """
    def insert_delta_log(self,    action,
                            delta       = 'Create',
                            path        = '',
                            from_path   = '',
                            to_path     = '',
                            is_dir      = 0,
                            size        = 0
                            ):

        account     = self.current_user['account']
        update_time = utils.get_timestamp()
        delta_poolid = self.current_user['poolid']

        if not delta_poolid is None:
            delta_db_path = '%s/history/%s/delta.db' % (options.storage_access_point,delta_poolid)
            logging.info("owner delta_poolid: %s ... ", delta_poolid)
            delta_conn = sqlite3.connect(delta_db_path)
            dbo_delta = DboDelta(delta_conn)
            dbo_delta.save_log(action,delta,path,from_path,to_path,account,update_time,method,is_dir,size)

        # duplicate log for share folder.
        # todo:
        # path need convert to relative with share folder local path.
        if len(path) > 0:
            # single path.
            # todo:
            #   need handle delete parent event.
            is_cross_owner_pool, share_delta_poolid = self.get_share_poolid(path)
            if not share_delta_poolid is None:
                delta_db_path = '%s/history/%s/delta.db' % (options.storage_access_point,share_delta_poolid)
                delta_conn = sqlite3.connect(delta_db_path)
                dbo_delta = DboDelta(delta_conn)
                dbo_delta.save_log(action,delta,path,from_path,to_path,account,update_time,method,is_dir,size)
        
        if len(from_path) > 0 and len(to_path) >0:
            # double path.
            # (case 1) for copy event, add files.
            # (case 2) for move event, from_path and to_path not same pool, do delete / add files event.
            # (case 3) for move event, from_path and to_path not same pool, do mvoe files event.
            is_cross_owner_pool, from_share_delta_poolid = self.get_share_poolid(from_path)
            is_cross_owner_pool, to_share_delta_poolid = self.get_share_poolid(to_path)
            
            # (case 1 & case 2)
            action      = 'UploadFile'
            delta       = 'Create'
            
            # (case 2)
            action      = 'FileDelete'
            delta       = 'Delete'
            
            # (case 3)
            # directly by pass owner event.
            pass
    """

    # return:
    #       True: Save done.
    #       False: Save fail.
    def add_path(self,     
                    tag         = 'file',
                    poolid      = 0,
                    path        = '',
                    doc_id      = 0,
                    account     = ''
                    ):

        update_time = utils.get_timestamp()
        ret = False
        errorMessage = ""
        try:
            sql = "DELETE FROM delta WHERE poolid=? and path=?"
            cursor = self.conn.execute(sql, (poolid,path,))

            sql = "INSERT INTO delta (tag,poolid,path,doc_id,account,update_time) VALUES (?, ?, ?, ?, ?, ?)"
            cursor = self.conn.execute(sql, (tag,poolid,path,doc_id,account,update_time,))
            self.conn.commit()
            ret = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            errorMessage = "{}".format(error)
            logging.info("sqlite error: %s", errorMessage)
            #raise
        return ret, errorMessage


    # return:
    #       True: Update as 'deleted' successfully.
    #       False: Update as 'deleted' fail.
    def delete_path(self, path='', account = ''):

        update_time = utils.get_timestamp()
        ret = False
        errorMessage = ""
        try:
            sql = "UPDATE delta set tag='deleted', update_time=? WHERE poolid=? and path=?"
            cursor = self.conn.execute(sql, (update_time, poolid, path,))
            self.conn.commit()
            ret = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            errorMessage = "{}".format(error)
            logging.info("sqlite error: %s", errorMessage)
            #raise
        return ret, errorMessage