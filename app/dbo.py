﻿import sqlite3
import datetime
import time
import logging

#data object for Debug
#############################################################
class BaseTable():
    sql_return_fields = ""
    sql_table_name = ""
    sql_primary_key = ""
    sql_inner_join_tables = ""
    conn = None

    def __init__(self, db_conn):
        #if db_path:
        #    self.conn = sqlite3.connect(db_path)
        if db_conn:
            self.conn = db_conn

    def vacuum(self):
        self.conn.execute("vacuum;")

    # return:
    #       0: not exist.
    #       1: exist.
    def pk_exist( self, pk_value):
        cursor = self.conn.execute('SELECT '+ self.sql_primary_key +' FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=? LIMIT 1', (pk_value,))
        result = 0
        for row in cursor:
            result = 1
        return result


    # input:
    #       pk_value: primary key value
    # return:
    #       rowcount: total count
    #       recorset: dictionary
    #       error_code: error code
    #       error_message: error message
    def query_id( self, pk_value ):
        in_dic = {}
        in_dic[self.sql_primary_key] = pk_value
        return self.query(in_dic)

        
    # input:
    #       order_by: how to sort output field.
    #       page: target page to show.
    #       pagesize: how many rows per page.
    #       server_host_name: server_host_name
    # return:
    #       rowcount: total count
    #       recorset: dictionary
    #       error_code: error code
    #       error_message: error message
    def query( self, in_dic ):
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0

        order_by_string = ''
        if in_dic.get('order_by', '') != '':
            order_by_string = ' ORDER BY ' + in_dic['order_by']

        limit_string = ''
        page = in_dic.get('page', 0)
        pagesize = in_dic.get('pagesize', 0)
        if page > 0 and pagesize > 0:
            offset = (page-1) * pagesize
            limit_string = ' LIMIT ? OFFSET ?' % (str(pagesize), str(offset))
        else:
            #print 'page paramater error'
            pass

        where_string = ''
            
        if in_dic.get(self.sql_primary_key, '') != '':
            if where_string  != '':
                where_string += ' AND '
            where_string += self.sql_primary_key +' = ' + str(in_dic[self.sql_primary_key]).replace("'", "''") + ""

        sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name
        if sql_inner_join_tables:
            sql += self.sql_inner_join_tables
        sql_count = 'SELECT count(*) FROM '+ self.sql_table_name
        if sql_inner_join_tables:
            sql_count += self.sql_inner_join_tables
        if where_string  != '':
            sql += ' WHERE ' + where_string
            sql_count += ' WHERE ' + where_string
        sql += order_by_string
        sql += limit_string
        #print 'SQL:' + sql
        try:
            cursor = self.conn.execute(sql_count, )
            for row in cursor:
                out_dic['rowcount'] =res[0]
            cursor = self.conn.execute(sql, )
            out_dic['recordset'] =self.get_dict_by_cursor(cursor)
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
        return out_dic


    # return:
    #       dictionary
    def get_dict_by_cursor( self, cursor):
        one=False
        r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        return (r[0] if r else None) if one else r




    # return:
    #       1: delete successfully.
    #       0: fail.
    def delete( self, pk_value):
        result = 0
        try:
            self.conn.execute('DELETE FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=?;', (pk_value,))
            self.conn.commit()
            result = 1
        except Exception as error:
            print("Error: {}".format(error))
            #result = error.args[0]
            raise
        return result

        
    # return:
    #       rowcount
    def get_rowcount( self):
        cursor = self.conn.execute('SELECT count(*) FROM '+ self.sql_table_name, )
        for row in cursor:
            total_rows=res[0]
        return total_rows



#data object for Account
#############################################################
class DboAccount(BaseTable):
    sql_return_fields = "account,email,owner"
    sql_table_name = "account"
    sql_primary_key = "account"


    # return:
    #       1: insert successfully.
    #    else: database error code.
    def save( self, admin_id, admin_pwd, is_owner ):
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0

        result = 0
        try:
            self.conn.execute("INSERT INTO account (account,password,is_owner) VALUES (?,?,?)", (admin_id, admin_pwd, is_owner))
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
    #       0: token valid.
    #       1: token not exist.
    #      10: token expire.
    #    else: database error code.
    def check_token( self, token_id):
        cursor = self.conn.execute('SELECT account FROM token WHERE token=? LIMIT 1', (token_id,))
        result=0
        out_dic = None
        for row in cursor:
            result=1
            sql = 'SELECT '+ self.sql_return_fields +' FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=? LIMIT 1'
            cursor = self.conn.execute(sql, (row[0],))
            out_dic = self.get_dict_by_cursor(cursor)[0]
        #return result
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
            self.conn.execute(sql, (token_id, admin_id, ip_address, int(time.time() * 1000),))
            self.conn.commit()
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            #raise
        return result

#data object for Account
#############################################################
class DboDelta(BaseTable):
    sql_return_fields = "account,email,owner"
    sql_table_name = "account"
    sql_primary_key = "account"