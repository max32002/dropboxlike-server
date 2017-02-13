import logging
from app.dbo.basetable import BaseTable

#data object for Account
#############################################################
class DboChunkUpload(BaseTable):
    sql_return_fields = "session_id,expires,owner"
    sql_table_name = "chunk_upload"
    sql_primary_key = "session_id"
    sql_create_table = '''
CREATE TABLE IF NOT EXISTS `chunk_upload` (
    `session_id`    varchar NOT NULL PRIMARY KEY,
    `expires` DATETIME,
    `owner` varchar NOT NULL
);
    '''


    # return:
    #       True: inser successfurlly.
    #       False: login successfully.
    def session_start(self,session_id, owner, autocommit=True):
        ret = False
        errorMessage = ""

        try:
            #[TODO]:
            #session id maybe conflict.

            sql = "INSERT INTO chunk_upload (session_id,expires,owner) VALUES (?, datetime('now'), ?)"
            self.conn.execute(sql, (session_id,owner,))
            if autocommit:
                self.conn.commit()
            ret = True
        except Exception as error:
            #except sqlite3.IntegrityError:
            #except sqlite3.OperationalError, msg:
            errorMessage = "{}".format(error)
            logging.info("sqlite error: %s", errorMessage)
            #raise

        return ret, errorMessage
