#!/usr/bin/env python
#encoding=utf-8
from app.handlers import BaseHandler
import logging
import json
import os
from tornado.options import options
from app.controller.meta_manager import MetaManager

class FileCreateFolderHandler(BaseHandler):
    metadata_manager = None

    def post(self):
        self.set_header('Content-Type','application/json')

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        if is_pass_check:
            is_pass_check = False
            try :
                _body = json.loads(self.request.body)
                is_pass_check = True
            except Exception:
                errorMessage = "wrong json format"
                errorCode = 1001
                pass

        path = None
        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'path' in _body:
                        path = _body['path']
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1002

        if is_pass_check:
            ret, errorMessage = self.check_path(path)
            if not ret:
                is_pass_check = False
                errorCode = 1010

        if is_pass_check:
            if len(path)==0:
                errorMessage = "path is empty"
                errorCode = 1013
                is_pass_check = False
                    
        if is_pass_check:
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

            if os.path.exists(self.metadata_manager.real_path):
                # path exist
                errorMessage = "path is exist"
                errorCode = 1020
                is_pass_check = False

        if is_pass_check:
            logging.info('user create real path at:%s' % (self.metadata_manager.real_path))
            self._createFolder(self.metadata_manager.real_path)

            # update metadata. (owner)
            is_pass_check, out_dict, errorMessage, errorCode = self.metadata_manager.add_metadata(path,is_dir=1)
            if not is_pass_check:
                # client need to check error code 1022, it's folder metadata exist.
                errorCode = 1020 + errorCode

        query_result = None
        if is_pass_check:
            # start to get metadata (owner)
            query_result = self.metadata_manager.get_path()
            if query_result is None:
                errorMessage = "metadata not found"
                errorCode = 1040
                is_pass_check = False

                # [TODO]:
                # real path exist, but database not exist.
                # reture error or sync database from real path.
                pass

        if is_pass_check:
            self.write(query_result)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))

    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

