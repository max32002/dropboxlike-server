from dbo.basetable import BaseTable
from lib import utils
import logging

#data object for Account
#############################################################
class DboAccount(BaseTable):
    sql_return_fields = "account,password,title,is_owner"
    sql_table_name = "users"
    sql_primary_key = "account"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `users` (
    `account`   TEXT NOT NULL PRIMARY KEY,
    `password`  TEXT NOT NULL,
    `title`   TEXT NULL,
    `is_owner` INTEGER,
    `createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']
    dbo_token = None

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)
        self.dbo_token = DboToken(db_conn)


    # return:
    #       True: insert successfully.
    #       False: fail
    def new_user( self, is_owner ):
        account = utils.get_token()
        while self.pk_exist(account):
            account = utils.get_token()
        password = utils.get_token()
        ret = self.save(account, password, is_owner)
        return ret, account, password


    # return:
    #       True: insert successfully.
    #       False: fail
    def save( self, account, password, is_owner ):
        result = False
        try:
            # start to insert.
            sql = "INSERT INTO users(account,password,is_owner) VALUES (?,?,?)"
            self.conn.execute(sql, (account, password, is_owner,))
            self.conn.commit()
            result = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            #raise
            pass
        return result


    # return:
    #       False: login fail.
    #       True: login successfully.
    def login( self, account, password ):
        sql = 'SELECT account FROM account WHERE account=? and password=? LIMIT 1'
        cursor = self.conn.execute(sql, (account, password,))
        ret=False
        for row in cursor:
            ret=True
        return ret


    # return:
    #    None: token not exist.
    #    account info dict: token valid.
    def check_token( self, token_id):
        ret = None
        cursor = self.conn.execute('SELECT account FROM token WHERE token=? LIMIT 1', (token_id,))
        for row in cursor:
            ret=row[0]
        return ret

    def get_pool_list( self, account):
        out_dic = None
        for row in cursor:
            sql = 'SELECT * FROM pool WHERE ownerid = ?'
            cursor = self.conn.execute(sql, (account,))
            if not cursor is None:
                out_dic = self.get_dict_by_cursor(cursor)
        return out_dic 


    # return:
    #       0: insert successfully.
    #    else: database error code.
    def save_token( self, token_id, account, ip_address):
        result = False
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "INSERT INTO token (token, account, ip_address, create_datetime) VALUES (?, ?, ?, ?)"
            self.conn.execute(sql, (token_id, account, ip_address, utils.get_timestamp(),))
            self.conn.commit()
            result = True
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
    sql_return_fields = "token.token,token.account,token.ip_address,token.createdTime"
    sql_table_name = "token"
    sql_primary_key = "token"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `token` (
    `token` TEXT NOT NULL,
    `account`   TEXT NOT NULL,
    `ip_address`    TEXT NULL,
    `createdTime` DATETIME NULL,
    PRIMARY KEY(token)
);
    '''
