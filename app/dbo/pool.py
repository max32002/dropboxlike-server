from app.dbo.basetable import BaseTable
from app.dbo import dbconst
import logging

#data object for pool
#############################################################
class DboPool(BaseTable):
    sql_return_fields = "poolid,ownerid,is_root"
    sql_table_name = "pool"
    sql_primary_key = "poolid"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pool` (
    `poolid` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `ownerid` TEXT,
    `is_root`  INTEGER,
    `createdTime` DATETIME NULL
);
    '''

    sql_create_index = ['''
    ''']

    def add(self, ownerid, is_root):
        result = False
        lastrowid = 0
        try:
            # insert master
            sql = "INSERT INTO pool (ownerid,is_root,createdTime) VALUES (?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (ownerid, is_root,))
            lastrowid = cursor.lastrowid
            #print "lastrowid", lastrowid
            self.conn.commit()
            result = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #logging.error("sql: %s", "{}".format(sql))
            #raise
        return result, lastrowid


    def get_root_pool( self, account):
        ret = None
        for row in cursor:
            sql = 'SELECT poolid FROM pool WHERE ownerid = ? and is_root=1 LIMIT 1'
            cursor = self.conn.execute(sql, (account,))
            for row in cursor:
                ret=row[0]
        return ret 



#data object for pool
#############################################################
class DboPoolSubscriber(BaseTable):
    sql_return_fields = "account,poolid,localpoolname,can_edit,status,createdTime"
    sql_table_name = "pool_subscriber"
    sql_primary_key = "account"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pool_subscriber` (
    `account`   TEXT NOT NULL,
    `poolid`    INTEGER NOT NULL,
    `localpoolname` TEXT NOT NULL,
    `can_edit`  INTEGER NOT NULL,
    `status`    INTEGER,
    `createdTime` DATETIME NULL,
    PRIMARY KEY(account, poolid)
);
    '''
    
    sql_create_index = ['''
    CREATE INDEX IF NOT EXISTS pool_subscriber_account ON pool_subscriber(account);
    ''']

    def add(self, account, poolid, localpoolname, can_edit, status):
        result = False
        try:
            # insert master
            sql = "INSERT INTO pool_subscriber (account, poolid, localpoolname, can_edit, status, createdTime) VALUES (?,?,?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (account, poolid, localpoolname, can_edit, status,))
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



    # return:
    #   (is_cross_owner_pool, poolid)
    #   is_cross_owner_pool: <True, False>
    #   poolid: pool id
    #
    #     PS1: each account should only have a owner(status=1) pool.
    #     PS2: only need to check shared (status=100) pool.
    #     PS3: shared(status=100) pool need to know parent folder is disappear! (move or delete action).
    #     PS4: copy command is not allow to do overwrite, so, only delete command effect share folder in sub-folder.
    def find_share_poolid( self, account, path):
        result = None
        is_cross_owner_pool = False
        try:
            sql = "SELECT poolid,localpoolname FROM pool_subscriber WHERE account=? AND status>=?"
            cursor = self.conn.execute(sql, (account,dbconst.POOL_STATUS_SHARED))
            for row in cursor:
                db_path = row[1] + "/"
                input_path = path + "/"
                # case 1: Database is shorter than path.
                # case 2: Database is equal with path.
                if input_path.startswith(db_path):
                    result=row[0]
                else:
                    # case 3: input path is shorter than path.
                    #       : only need to handle parent move.
                    if db_path.startswith(input_path):
                        is_cross_owner_pool = True
                        result=row[0]

            if result is None:
                # get default unshared pool
                pass
                    
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return (is_cross_owner_pool, result)


