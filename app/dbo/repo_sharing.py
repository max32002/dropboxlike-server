import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboRepoSharing(BaseTable):
    sql_return_fields = "share_code,password"
    sql_table_name = "repo_sharing"
    sql_primary_key = "share_code"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `repo_sharing` (
`share_code`   TEXT NOT NULL PRIMARY KEY,
`password`   TEXT NULL,
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
    def add(self, share_code, password):
        result = False
        try:
            # insert master
            sql = "INSERT INTO repo_sharing (share_code, password,createdTime) VALUES (?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (share_code, password))

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

    def match(self, share_code, password):
        where = "share_code='" + share_code.replace("'", "''") + "' and password='" + password.replace("'", "''") + "'"
        #print "sql where:",where
        return self.first(where=where)
