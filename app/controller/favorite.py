from app.handlers import BaseHandler
from tornado.options import options
import logging
import sqlite3
from app.dbo.metadata import DboMetadata
from app.lib import utils
import json
import os

class FavoriteHandler(BaseHandler):
    '''!Metadata API Controller'''

    def get(self, path):
        """metadata a path
        @param path file path
        @retval Object http response
        """ 
        self.set_header('Content-Type','application/json')

        path = path.lstrip('/')
        real_path = None
        is_shared_folder = False

        status_code = 200
        error_dict = None
        status_code, error = self.check_path(path,is_shared_folder)

        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))
            logging.info('user query metadata path:%s, at real path: %s' % (path, real_path))

        if status_code == 200:
            if not os.path.exists(real_path):
                status_code = 400
                error_code = 123
                error_dict = dict(error_msg='path is not exist.',error_code=error_code)
            else:
                # path exist.
                pass

        if status_code == 200:
            # start to get metadata (owner)
            poolid = self.current_user['poolid']
            self.open_metadata(poolid)
            query_result = self.metadata_manager.query(path)
            if not query_result is None:
                #self.write(query_result)
                self.write("[]")
            else:
                # todo:
                # real path exist, but database not exist.
                # reture error or sync database from real path.
                pass
        else:
            self.set_status(status_code)
            self.write(error_dict)

