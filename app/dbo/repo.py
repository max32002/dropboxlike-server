import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboRepo(BaseTable):
    sql_return_fields = "repo_token,title,status"
    sql_table_name = "repo"
    sql_primary_key = "repo_token"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `repo` (
`repo_token`   TEXT NOT NULL PRIMARY KEY,
`title`   TEXT NULL,
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
    def add(self, title, repo_token):
        result = False
        try:
            # insert master
            sql = "INSERT INTO repo (title, repo_token, status,createdTime) VALUES (?,?, 0,datetime('now'));"
            cursor = self.conn.execute(sql, (title, repo_token,))

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
