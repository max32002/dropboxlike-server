import logging
from dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboPincode(BaseTable):
    sql_return_fields = "pincode,password,sn,createdTime"
    sql_table_name = "pincode"
    sql_primary_key = "pincode"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pincode` (
`pincode`   TEXT NOT NULL PRIMARY KEY,
`password` TEXT NOT NULL,
`sn` TEXT NOT NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    def add(self, pincode, password, sn):
        result = 0
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            # insert master
            sql = "INSERT INTO pincode (pincode,password,sn,createdTime) VALUES (?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (pincode,password,sn))

            self.conn.commit()
            out_dic['lastrowid'] = cursor.lastrowid
            result = 1
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            logging.info("sql: %s", "{}".format(sql))
            #raise
        return result, out_dic


    def match(self, pincode, password):
        where = "pincode='" + pincode.replace("'", "''") + "' and password='" + pincode.replace("'", "''") + "'"
        return self.first(where=where)
