from app.handlers import BaseHandler
from tornado.options import options
import logging
from app.lib import utils

class AccountInfoHandler(BaseHandler):
    ''' Acount Info API Controller'''

    def get(self):
        self.set_header('Content-Type','application/json')

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        if is_pass_check:
            self.set_status(200)
            dict_usage = {'used':0,'trash':0,'quota':0}
            self.write(dict_usage)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
