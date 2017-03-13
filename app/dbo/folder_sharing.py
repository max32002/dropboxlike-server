import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboFolderSharing(BaseTable):
    sql_return_fields = "share_code,password,poolid"
    sql_table_name = "folder_sharing"
    sql_primary_key = "share_code"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `folder_sharing` (
`share_code`   TEXT NOT NULL PRIMARY KEY,
`password`   TEXT NULL,
`poolid` INTEGER NOT NULL,
`can_edit` INTEGER NOT NULL,
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
    def add(self, share_code, password, poolid, can_edit):
        result = False
        try:
            # insert master
            sql = "INSERT INTO folder_sharing (share_code, password, poolid, can_edit, createdTime) VALUES (?,?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (share_code, password, poolid, can_edit))
            self.conn.commit()
            result = True
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return result

    def match(self, share_code, password):
        where = "share_code='" + share_code.replace("'", "''") + "' and password='" + password.replace("'", "''") + "'"
        #print "sql where:",where
        return self.first(where=where)
