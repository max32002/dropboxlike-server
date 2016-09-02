import sqlite3
#import logging

#############################################################
class DatabaseError:
    @classmethod
    def INSERT_INPUT_EMPTY(cls):
        return "INSERT_INPUT_EMPTY"

    def UPDATE_INPUT_EMPTY(cls):
        return "UPDATE_INPUT_EMPTY"

    def DELETE_INPUT_EMPTY(cls):
        return "DELETE_INPUT_EMPTY"

    def QUERY_INPUT_EMPTY(cls):
        return "QUERY_INPUT_EMPTY"

    def DATABASE_IS_LOCKED(cls):
        return "database is locked"

    def LOCAL_METADATA_PARENT_NOT_EXIST(cls):
        return 'parent node not exist.'

#data object for Debug
#############################################################
class BaseTable():
    sql_return_fields = ""
    sql_table_name = ""
    sql_primary_key = ""
    sql_inner_join_tables = ""
    sql_create_table = None
    sql_create_index = []
    conn = None

    def __init__(self, db_conn):
        #if db_path:
        #    self.conn = sqlite3.connect(db_path)
        if db_conn:
            self.conn = db_conn
        if self.sql_create_table is not None:
            self.conn.execute(self.sql_create_table)
        for create_index_string in self.sql_create_index:
            if create_index_string is not None:
                self.conn.execute(create_index_string)

    def vacuum(self):
        sql = "vacuum;"
        self.conn.execute(sql)
        self.conn.commit()

    def drop(self):
        sql = 'drop table ' + self.sql_table_name + ';'
        self.conn.execute(sql)
        self.conn.commit()

    def empty(self):
        sql = 'delete from ' + self.sql_table_name + ';'
        self.conn.execute(sql)
        self.conn.commit()

    # return:
    #       0: not exist.
    #       1: exist.
    def pk_exist( self, pk_value):
        cursor = self.conn.execute('SELECT '+ self.sql_primary_key +' FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=? LIMIT 1', (pk_value,))
        result = 0
        for row in cursor:
            result = 1
        return result

    # return:
    #       1: delete successfully.
    #       0: fail.
    def pk_delete( self, pk_value):
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
    def query( self, in_dic, query_rowcount=False):
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
            if query_rowcount:
                cursor = self.conn.execute(sql_count, )
                for row in cursor:
                    out_dic['rowcount'] =row[0]
            cursor = self.conn.execute(sql, )
            out_dic['recordset'] =self.get_dict_by_cursor(cursor)
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            #logging.info("sqlite error: %s", "{}".format(error))
        return out_dic


    # return:
    #       dictionary
    def get_dict_by_cursor( self, cursor):
        one=False
        r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        return (r[0] if r else None) if one else r

    # return:
    #       rowcount
    def rowcount(self):
        cursor = self.conn.execute('SELECT count(*) FROM '+ self.sql_table_name, )
        for row in cursor:
            total_rows=row[0]
        return total_rows

    # return:
    def save(self):
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "INSERT INTO "+ self.sql_table_name +" ("+self.sql_primary_key+") VALUES (null)"
            cursor = self.conn.execute(sql)
            self.conn.commit()
            out_dic['lastrowid'] = cursor.lastrowid
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            #raise
        return out_dic
