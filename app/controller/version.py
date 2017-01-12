from app.handlers import BaseHandler
from tornado.options import options
import logging

class VersionHandler(BaseHandler):

    def get(self):
        self.set_header('Content-Type','application/json')

        self.set_status(200)
        data = {'versionCode':options.versionCode, 'versionName':options.versionName, 'claimed':self.application.claimed}
        self.write(data)
