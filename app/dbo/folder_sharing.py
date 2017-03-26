import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboFolderSharing(BaseTable):
    sql_return_fields = "share_code,password,poolid,poolname,can_edit,share_status"
    sql_table_name = "folder_sharing"
    sql_primary_key = "share_code"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `folder_sharing` (
`share_code`   TEXT NOT NULL PRIMARY KEY,
`password`   TEXT NULL,
`poolid` INTEGER NOT NULL,
`poolname` TEXT NOT NULL,
`can_edit` INTEGER NOT NULL,
`share_status` INTEGER NOT NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    CREATE INDEX IF NOT EXISTS folder_sharing_poolid ON folder_sharing(poolid);
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    # return:
    #       False: add fail.
    #       True: add successfully.
    def add(self, share_code, password, poolid, poolname, can_edit):
        result = False
        try:
            # insert master
            sql = "INSERT INTO folder_sharing (share_code, password, poolid, poolname, can_edit, share_status, createdTime) VALUES (?,?,?,?,?,1,datetime('now'));"
            cursor = self.conn.execute(sql, (share_code, password, poolid, poolname, can_edit))
            self.conn.commit()
            result = True
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return result

    def match(self, share_code, password):
        where = "share_code='" + share_code.replace("'", "''") + "' and password='" + password.replace("'", "''") + "' and share_status=1"
        #print "sql where:",where
        return self.first(where=where)

    def list_share_code(self, poolid):
        where = "poolid=" + str(poolid).replace("'", "''")
        #print "sql where:",where
        return self.all(where=where)

    def switch_share_status(self, poolid, share_status):
        result = False
        try:
            sql = "UPDATE folder_sharing SET share_status=? WHERE poolid=?;"
            cursor = self.conn.execute(sql, (share_status, poolid))
            self.conn.commit()
            result = True
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return result

    def delete_pool(self, poolid):
        result = False
        try:
            sql = "DELETE FROM folder_sharing WHERE poolid=?;"
            cursor = self.conn.execute(sql, (poolid, ))
            self.conn.commit()
            result = True
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return result
