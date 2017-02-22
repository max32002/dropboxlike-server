import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboPincode(BaseTable):
    sql_return_fields = "pincode,serialnumber,sn,createdTime"
    sql_table_name = "pincode"
    sql_primary_key = "pincode"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pincode` (
`pincode`   TEXT NOT NULL PRIMARY KEY,
`serialnumber` TEXT NOT NULL,
`sn` TEXT NOT NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    def add(self, pincode, serialnumber, sn):
        result = False
        try:
            # insert master
            sql = "INSERT INTO pincode (pincode,serialnumber,sn,createdTime) VALUES (?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (pincode,serialnumber,sn))

            self.conn.commit()
            result = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #logging.error("sql: %s", "{}".format(sql))
            #raise
        return result


    def match(self, pincode, serialnumber):
        where = "pincode='" + pincode.replace("'", "''") + "' and serialnumber='" + serialnumber.replace("'", "''") + "'"
        #print "sql where:",where
        return self.first(where=where)


#data object for Drive
#############################################################
class DboPincodeLog(BaseTable):
    sql_return_fields = "pincode,serialnumber,request_id,client_md5,remoteIp,createdTime"
    sql_table_name = "pincode_log"
    sql_primary_key = "id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pincode_log` (
`id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
`pincode`   TEXT NOT NULL,
`serialnumber` TEXT NOT NULL,
`request_id` INTEGER NOT NULL,
`client_md5` TEXT NOT NULL,
`remoteIp` TEXT NOT NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    def add(self, pincode, serialnumber, request_id, client_md5, remoteIp):
        result = False
        try:
            # insert master
            sql = "INSERT INTO pincode_log (pincode,serialnumber,request_id,client_md5,remoteIp,createdTime) VALUES (?,?,?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (pincode, serialnumber, request_id, client_md5, remoteIp))

            self.conn.commit()
            result = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #logging.error("sql: %s", "{}".format(sql))
            #raise
        return result
