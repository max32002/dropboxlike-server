import logging
from app.dbo.basetable import BaseTable
from tornado.options import options


#data object for Schema
#############################################################
class DboSchemaVersion(BaseTable):
    sql_return_fields = "version"
    sql_table_name = "schema_version"
    sql_primary_key = "version"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `schema_version` (
`version`   INTEGER NOT NULL PRIMARY KEY
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)


    # auto upgrade old version database.
    def auto_upgrade(self):
        if self.rowcount()==0:
            # empty database, insert current version code.
            self.add(options.database_schema_version)

    # return:
    #       0: login fail.
    #       1: login successfully.
    def add(self, code):
        result = 0
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            # insert master
            sql = "INSERT INTO schema_version (version) VALUES (?);"
            cursor = self.conn.execute(sql, (code,))

            self.conn.commit()
            out_dic['lastrowid'] = cursor.lastrowid
            result = 1
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            logging.info("sql: %s", "{}".format(sql))
            #raise
        return result, out_dic

