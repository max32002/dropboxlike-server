#!/usr/bin/env python
#encoding=utf-8
from basetable import BaseTable
import dbconst
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
            logging.error("sqlite error: %s", "{}".format(error))
            #logging.error("sql: %s", "{}".format(sql))
            #raise
        return result, lastrowid


    def get_root_pool( self, account):
        ret = None
        try:
            sql = 'SELECT poolid FROM pool WHERE ownerid = ? and is_root=1 LIMIT 1'
            cursor = self.conn.execute(sql, (account,))
            for row in cursor:
                ret=row[0]
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #logging.error("sql: %s", "{}".format(sql))
            #raise
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
        ret_dict = None
        try:
            sql = "SELECT poolid,localpoolname,can_edit FROM pool_subscriber WHERE account=? AND status in (?,?)"
            cursor = self.conn.execute(sql, (account,dbconst.POOL_STATUS_SHARED,dbconst.POOL_STATUS_SHARED_ACCEPTED))
            for row in cursor:
                db_path = row[1] + "/"
                input_path = path + "/"
                # case 1: Database is shorter than path.
                # case 2: Database is equal with path.
                if input_path.startswith(db_path):
                    ret_dict = {}
                    ret_dict['poolid']=row[0]
                    ret_dict['poolname']=row[1]
                    ret_dict['can_edit']=row[3]
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return ret_dict


