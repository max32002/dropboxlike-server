﻿import logging
from dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboDrive(BaseTable):
    sql_return_fields = "sn,title,drive_token,status"
    sql_table_name = "drive"
    sql_primary_key = "sn"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `drive` (
`sn`   TEXT NOT NULL PRIMARY KEY,
`title`   TEXT NULL,
`drive_token`   TEXT NULL,
`status` INTEGER NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    # return:
    #       False: add fail.
    #       True: add successfully.
    def add(self, sn, title, drive_token):
        result = False
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            # insert master
            sql = "INSERT INTO drive (sn, title, drive_token, status,createdTime) VALUES (?,?,?, 0,datetime('now'));"
            cursor = self.conn.execute(sql, (sn,))

            self.conn.commit()
            out_dic['lastrowid'] = cursor.lastrowid
            result = True
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

