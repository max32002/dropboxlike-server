import logging
from dbo.basetable import BaseTable

#data object for Account
#############################################################
class DboChunkUpload(BaseTable):
    sql_return_fields = "upload_id,path,bytes,offset,mtime,expires,owner"
    sql_table_name = "chunk_upload"
    sql_primary_key = "upload_id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `chunk_upload` (
    `upload_id`    varchar NOT NULL PRIMARY KEY,
    `path` varchar NOT NULL,
    `bytes` integer NOT NULL,
    `offset` integer NOT NULL,
    `mtime` varchar,
    `expires` integer,
    `owner` varchar NOT NULL
);
    '''


    # return:
    #       0: login fail.
    #       1: login successfully.
    def save(self,upload_id,path,bytes,offset,mtime,expires,owner):
        result = 0
        out_dic = {}
        out_dic['error_code'] = ''
        out_dic['rowcount'] = 0
        try:
            sql = "INSERT INTO chunk_upload (upload_id,path,bytes,offset,mtime,expires,owner) VALUES (?, ?, ?, ?, ?, ?, ?)"
            self.conn.execute(sql, (upload_id,path,bytes,offset,mtime,expires,owner,))
            self.conn.commit()
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            #print("Error: {}".format(error))
            out_dic['error_code'] = error.args[0]
            out_dic['error_message'] = "{}".format(error)
            logging.info("sqlite error: %s", "{}".format(error))
            #raise
        return result
