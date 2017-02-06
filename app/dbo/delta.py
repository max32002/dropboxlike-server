import logging
from app.dbo.basetable import BaseTable

#data object for Account
#############################################################
class DboDelta(BaseTable):
    sql_return_fields = "update_time,action,path,from_path,to_path,method,is_dir,size,account"
    sql_table_name = "delta"
    sql_primary_key = "delta_id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `delta` (
    `delta_id`  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `delta`    TEXT,
    `action`    TEXT,
    `path`  TEXT,
    `from_path` TEXT,
    `to_path`   TEXT,
    `method`    TEXT,
    `is_dir`    INTEGER,
    `size`  INTEGER,
    `account`   TEXT NOT NULL,
    `update_time`   INTEGER
);
    '''
    sql_create_index = ['''
CREATE INDEX IF NOT EXISTS delta_timestamp ON delta(account,update_time);
    ''']

    """
    def insert_delta_log(self,    action,
                            delta       = 'Create',
                            path        = '',
                            from_path   = '',
                            to_path     = '',
                            method      = 'POST',
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
    #       0: login fail.
    #       1: login successfully.
    def save_log(self,     action, 
                           delta       = 'Create',
                           path        = '',
                           from_path   = '',
                           to_path     = '',
                           account     = '',
                           update_time = 0,
                           method      = 'POST',
                           is_dir      = 0,
                           size        = 0,
                           ):
        result = 0
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "INSERT INTO delta (action,delta,path,from_path,to_path,account,update_time,method,is_dir,size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor = self.conn.execute(sql, (action,delta,path,from_path,to_path,account,update_time,method,is_dir,size,))
            self.conn.commit()
            out_dic['lastrowid'] = cursor.lastrowid
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            #raise
        return result
