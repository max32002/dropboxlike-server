#!/usr/bin/env python
#encoding=utf-8
import logging
from app.dbo.basetable import BaseTable


#data object for Drive
#############################################################
class DboTempLink(BaseTable):
    sql_return_fields = "link,poolid,doc_id,content_hash,createdTime"
    sql_table_name = "temp_link"
    sql_primary_key = "link"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `temp_link` (
`link`   TEXT NOT NULL PRIMARY KEY,
`poolid`  integer NOT NULL,
`doc_id`  integer NOT NULL,
`content_hash`  varchar,
`editor`   TEXT NOT NULL,
`createdTime` DATETIME NULL
);
    '''
    sql_create_index = ['''
    ''']

    def __init__(self, db_conn):
        BaseTable.__init__(self, db_conn)

    # return:
    #       False: add fail.
    #       True: add successfully.
    def add(self, link, poolid, doc_id, content_hash, editor):
        result = False
        try:
            # insert master
            sql = "INSERT INTO temp_link (link, poolid, doc_id, content_hash, editor,createdTime) VALUES (?,?,?,?,?,datetime('now'));"
            cursor = self.conn.execute(sql, (link, poolid, doc_id, content_hash, editor))

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

    # PURPOSE: clean expired temp_link.
    # Get a temporary link to stream content of a file. This link will expire in four hours and afterwards you will get 410 Gone. Content-Type of the link is determined automatically by the file's mime type.
    def clean_expire(self):
        pass
