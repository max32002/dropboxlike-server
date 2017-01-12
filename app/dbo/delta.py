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
