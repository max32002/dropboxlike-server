from app.handlers import BaseHandler
from tornado.options import options
import logging
from app.lib import utils
import os

class CursorHandler(BaseHandler):
    '''!Cursor API Controller'''

    def get(self):
        """metadata a path
        @param path file path
        @retval Object http response
        """ 
        self.set_header('Content-Type','application/json')

        status_code = 200
        error_dict = None

        if status_code == 200:
            dict_delta = {'cursor': utils.get_timestamp()}
            self.write(dict_delta)
        else:
            self.set_status(status_code)
            self.write(error_dict)



