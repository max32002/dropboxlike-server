from handlers import BaseHandler
from tornado.options import options
import logging
from lib import utils

class UsageHandler(BaseHandler):
    '''!Usage API Controller'''

    def get(self):
        """metadata a path
        @param path file path
        @retval Object http response
        """ 
        self.set_header('Content-Type','application/json')

        status_code = 200
        error_dict = None

        if status_code == 200:
            dict_usage = {'used':0,'trash':0,'quota':0}
            self.write(dict_usage)
        else:
            self.set_status(status_code)
            self.write(error_dict)
