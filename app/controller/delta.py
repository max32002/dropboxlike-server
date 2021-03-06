#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
from tornado.options import options
import logging
import sqlite3
from app.dbo.metadata import DboMetadata
from app.lib import utils
import json
import os

class DeltaHandler(BaseHandler):

    def post(self):
        self.set_header('Content-Type','application/json')
        cursor = None
        if self.has_argument('cursor'):
            cursor = self.get_argument('cursor')

        status_code = 200
        error_dict = None

        if status_code == 200:
            self.get_delta(cursor)

        else:
            self.set_status(status_code)
            self.write(error_dict)
            #self.write(dict(error=dict(message=errorMessage,code=errorCode)))

    def get_delta(self, cursor):

        # start to get metadata (owner)
        poolid = self.current_user['poolid']
        #self.open_metadata(poolid)
        #query_result = self.metadata_manager.query(path)
        query_result = None
        if not query_result is None:
            #self.write(query_result)
            #self.write("[]")
            pass
        else:
            # todo:
            # real path exist, but database not exist.
            # reture error or sync database from real path.
            pass

        dict_delta = {
'entries':[],
'cursor': utils.get_timestamp(),
'quota': 0,
'has_more': False
}
        self.write(dict_delta)
