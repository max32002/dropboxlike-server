from app.dbo.basetable import BaseTable
import logging

#data object for pool
#############################################################
class DboPool(BaseTable):
    sql_return_fields = "poolid,ownerid,type"
    sql_table_name = "pool"
    sql_primary_key = "poolid"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pool` (
    `poolid` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `ownerid` TEXT,
    `type`  INTEGER
);
    '''

    sql_create_index = ['''
    ''']

#data object for pool
#############################################################
class DboPoolSubscriber(BaseTable):
    sql_return_fields = "account,poolid,localpoolname,can_edit,status,create_datetime"
    sql_table_name = "pool_subscriber"
    sql_primary_key = "account"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `pool_subscriber` (
    `account`   TEXT NOT NULL,
    `poolid`    INTEGER NOT NULL,
    `localpoolname` TEXT NOT NULL,
    `can_edit`  INTEGER NOT NULL,
    `status`    INTEGER,
    `create_datetime`   INTEGER,
    PRIMARY KEY(account, poolid)
);
    '''
    
    sql_create_index = ['''
    CREATE INDEX IF NOT EXISTS pool_subscriber_account ON pool_subscriber(account);
    ''']






