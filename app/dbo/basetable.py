import sqlite3
#import logging
import datetime
import six

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

    def vacuum(self, autocommit=True):
        sql = "vacuum;"
        self.conn.execute(sql)
        if autocommit:
            self.conn.commit()

    def drop(self, autocommit=True):
        sql = 'drop table ' + self.sql_table_name + ';'
        self.conn.execute(sql)
        if autocommit:
            self.conn.commit()

    def empty(self, autocommit=True):
        sql = 'delete from ' + self.sql_table_name + ';'
        self.conn.execute(sql)
        if autocommit:
            self.conn.commit()

    # return:
    #       True: exist.
    #       False: not exist.
    def pk_exist( self, pk_value):
        cursor = self.conn.execute('SELECT '+ self.sql_primary_key +' FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=? LIMIT 1', (pk_value,))
        result = False
        for row in cursor:
            result = True
        return result

    # return:
    #       True: exist.
    #       False: not exist.
    def field_value_exist( self, field_name, field_value):
        cursor = self.conn.execute('SELECT '+ self.sql_primary_key +' FROM '+ self.sql_table_name +' WHERE '+ field_name +'=? LIMIT 1', (field_value,))
        result = False
        for row in cursor:
            result = True
        return result

    # return:
    #       True: delete successfully.
    #       False: fail.
    def pk_delete( self, pk_value, autocommit=True):
        result = False
        try:
            self.conn.execute('DELETE FROM '+ self.sql_table_name +' WHERE '+ self.sql_primary_key +'=?;', (pk_value,))
            if autocommit:
                self.conn.commit()
            result = True
        except Exception as error:
            print("Error: {}".format(error))
            #result = error.args[0]
            #raise
        return result


    # return:
    #       first data in dictionary
    def pk_query(self, data=None):
        where = self.sql_primary_key + "='" + str(data) + "'"
        if isinstance(data, six.integer_types):
            where = self.sql_primary_key + "=" + str(data) + ""
        return self.first(where=where)


    # return:
    def pk_save(self, autocommit=True):
        ret = False
        try:
            sql = "INSERT INTO "+ self.sql_table_name +" ("+self.sql_primary_key+") VALUES (null)"
            cursor = self.conn.execute(sql)
            if autocommit:
                self.conn.commit()
            ret = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            logging.error("sqlite error: %s", "{}".format(error))
            #raise
        return ret

        
    # input:
    #       order_by: how to sort output field.
    #       page: target page to show.
    #       pagesize: how many rows per page.
    #       server_host_name: server_host_name
    # return:
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
            #logging.error("sqlite error: %s", "{}".format(error))
        return out_dic


    # return:
    #       dictionary
    def get_dict_by_cursor( self, cursor):
        one=False
        r = [
                dict((cursor.description[i][0], (value.strftime('%Y-%m-%d %H:%M:%S') if isinstance(value, datetime.datetime) else value)) for i, value in enumerate(row)) for row in cursor.fetchall()
            ]
        return (r[0] if r else None) if one else r


    # return:
    #       all data in dictionary
    def all(self, where="", order_by="", limit=None):
        sql_return_fields = self.sql_return_fields
        if len(sql_return_fields) == 0:
            sql_return_fields = "*"
        if len(where) > 0:
            where = " WHERE " + where
        if len(order_by) > 0:
            where = " ORDER BY " + order_by
        if not limit is None:
            limit = " LIMIT %d" % limit
        else:
            limit = ""
        sql = 'SELECT %s FROM %s%s%s'  % (sql_return_fields, self.sql_table_name, where, limit)
        #print sql
        cursor = self.conn.execute(sql, )
        return self.get_dict_by_cursor(cursor)


    # return:
    #       first data in dictionary
    def first(self, where="",order_by=""):
        ret = None
        ret_array = self.all(where,order_by,limit=1)
        if not ret_array is None:
            if len(ret_array) > 0:
                ret = ret_array[0]
        return ret


    # return:
    #       rowcount
    def rowcount(self):
        sql = 'SELECT count(*) FROM '+ self.sql_table_name
        #print sql
        cursor = self.conn.execute(sql)
        total_rows = 0
        for row in cursor:
            total_rows=row[0]
        return total_rows

