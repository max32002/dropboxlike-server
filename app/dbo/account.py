from app.dbo.basetable import BaseTable
from app.dbo.pool import DboPool
from app.dbo.pool import DboPoolSubscriber
from app.lib import utils
from app.lib import misc
import logging

#data object for Account
#############################################################
class DboAccount(BaseTable):
    sql_return_fields = "account,password,title,is_owner,account_sn,security_answer_md5"
    sql_table_name = "users"
    sql_primary_key = "account"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `users` (
    `account`   TEXT NOT NULL PRIMARY KEY,
    `password`  TEXT NOT NULL,
    `title`   TEXT NULL,
    `is_owner` INTEGER,
    `account_sn`   TEXT NULL,
    `security_question`   TEXT NULL,
    `security_answer_md5`   TEXT NULL,
    `createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    dbo_token = None
    dbo_pool = None
    dbo_pool_subcriber = None

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)
        self.dbo_token = DboToken(db_conn)
        self.dbo_pool = DboPool(db_conn)
        self.dbo_pool_subcriber = DboPoolSubscriber(db_conn)


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
            logging.error("sqlite error: %s", "{}".format(error))
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
        sql = 'SELECT account FROM users WHERE account=? and password=? LIMIT 1'
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
        sql = 'SELECT account FROM token WHERE token=? LIMIT 1'
        cursor = self.conn.execute(sql, (token_id,))
        for row in cursor:
            ret=row[0]
        return ret

    def get_root_pool( self, account):
        return self.dbo_pool.get_root_pool(account)

    # return:
    #       0: insert successfully.
    #    else: database error code.
    def save_token( self, token_id, account, ip_address):
        return self.dbo_token.add(token_id, account, ip_address)

    # return:
    #   (is_cross_owner_pool, poolid)
    def find_share_poolid( self, account, path):
        return self.dbo_pool_subcriber.find_share_poolid(account, path)

    # return:
    #       False: update fail.
    #       True: update successfully.
    def account_sn_update(self, account, account_sn):
        result = False
        try:
            sql = "UPDATE users set account_sn=? WHERE account=?;"
            cursor = self.conn.execute(sql, (account_sn, account))
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
    #       False: update fail.
    #       True: update successfully.
    def security_update(self, account, security_question, security_answer):
        result = False
        try:
            security_answer_md5 = misc.md5_hash(security_answer)
            sql = "UPDATE users set security_question=?, security_answer_md5=? WHERE account=?;"
            cursor = self.conn.execute(sql, (security_question, security_answer_md5, account))
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
    #       False: reset fail.
    #       True: reset successfully.
    def reset_all_security_question(self):
        result = False
        try:
            sql = "UPDATE users set security_question=null, security_answer_md5=null;"
            #print "sql:",sql
            cursor = self.conn.execute(sql)
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

    def add( self, token_id, account, ip_address):
        result = False
        try:
            sql = "INSERT INTO token (token, account, ip_address, createdTime) VALUES (?, ?, ?, datetime('now'))"
            self.conn.execute(sql, (token_id, account, ip_address,))
            self.conn.commit()
            result = True
        except Exception as error:
            logging.error("sqlite error: %s", "{}".format(error))
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            #raise
        return result
