from dbo.basetable import BaseTable
from lib import utils
import logging

#data object for Account
#############################################################
class DboAccount(BaseTable):
    sql_return_fields = "account.account,account.accountname,account.email,account.owner"
    sql_table_name = "account"
    sql_primary_key = "account"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `account` (
    `account`   TEXT NOT NULL,
    `accountname`   TEXT NULL,
    `password`  TEXT NOT NULL,
    `email` TEXT,
    `owner` INTEGER,
    PRIMARY KEY(account)
);
    '''
    sql_create_index = ['''
CREATE INDEX IF NOT EXISTS account_login ON account(account,password);
    ''']
    dbo_token = None

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)
        self.dbo_token = DboToken(db_conn)

    # return:
    #       1: insert successfully.
    #    else: database error code.
    def save( self, admin_id, admin_name, admin_pwd, is_owner ):
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0

        result = 0
        try:
            # try to get not used uuid
            # // do something here.

            # start to insert.
            self.conn.execute("INSERT INTO account (account,accountname,password,is_owner) VALUES (?,?,?,?)", (admin_id, admin_name, admin_pwd, is_owner))
            self.conn.commit()
            result = 1
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            #raise
        return result


    # return:
    #       0: login fail.
    #       1: login successfully.
    def login( self, admin_id, admin_pwd ):
        cursor = self.conn.execute('SELECT account FROM account WHERE account=? and password=? LIMIT 1', (admin_id, admin_pwd))
        result=0
        for row in cursor:
            result=1
        return result


    # return:
    #    None: token not exist.
    #    account info dict: token valid.
    def check_token( self, token_id):
        cursor = self.conn.execute('SELECT account FROM token WHERE token=? LIMIT 1', (token_id,))
        result=0
        out_dic = None
        for row in cursor:
            result=1
            sql = 'SELECT '+ self.sql_return_fields +',pool.poolid, \'' + token_id + '\' as token FROM '+ self.sql_table_name +' INNER JOIN pool ON pool.ownerid = account.account WHERE account.account=? LIMIT 1'
            cursor = self.conn.execute(sql, (row[0],))
            if not cursor is None:
                out_dic = self.get_dict_by_cursor(cursor)[0]
        return out_dic 


    # return:
    #       0: insert successfully.
    #    else: database error code.
    def save_token( self, token_id, admin_id, ip_address):
        result = 0
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "INSERT INTO token (token, account, ip_address, create_datetime) VALUES (?, ?, ?, ?)"
            self.conn.execute(sql, (token_id, admin_id, ip_address, utils.get_timestamp(),))
            self.conn.commit()
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            #raise
        return result


    # return:
    # (is_cross_owner_pool, poolid)
    #  is_cross_owner_pool: <True, False>
    #  poolid: pool id
    #
    #     PS1: each account should only have a owner(status=10) pool.
    #     PS2: only need to check shared (status=11) pool.
    #     PS3: shared(status=11) pool need to know parent folder is disappear! (move or delete action).
    #     PS4: copy command is not allow to do overwrite, so, only delete command effect share folder in sub-folder.
    def find_share_poolid( self, account, path):
        result = None
        is_cross_owner_pool = False
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "SELECT poolid,localpoolname FROM account_pool WHERE account=? AND status=11"
            cursor = self.conn.execute(sql, (account,))
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
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            #raise
        return (is_cross_owner_pool, result)



#data object for token
#############################################################
class DboToken(BaseTable):
    sql_return_fields = "token.token,token.account,token.ip_address,token.create_datetime"
    sql_table_name = "token"
    sql_primary_key = "token"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `token` (
    `token` TEXT NOT NULL,
    `account`   TEXT NOT NULL,
    `ip_address`    TEXT NULL,
    `create_datetime`   INTEGER,
    PRIMARY KEY(token)
);
    '''
