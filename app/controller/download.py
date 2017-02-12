#!/usr/bin/env python
#fileencoding=utf-8

from app.handlers import BaseHandler
import logging
import json
from app.controller.meta_manager import MetaManager
import os

class DownloadHandler(BaseHandler):
    metadata_manager = None

    def post(self):
        self.set_header('Content-Type','application/json')

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        apiArg = self.request.headers.get("Dropboxlike-API-Arg")
        #logging.info('apiArg:%s ', apiArg)

        if is_pass_check:
            if apiArg is None:
                is_pass_check = False
                errorMessage = "wrong json format"
                errorCode = 1001

        _body = None
        if is_pass_check:
            is_pass_check = False
            try :
                _body = json.loads(apiArg)
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


        if is_pass_check:
            logging.info('download from real path at:%s' % (self.metadata_manager.real_path))

            # update metadata. (owner)
            if not os.path.exists(self.metadata_manager.real_path):
                errorMessage = "not_found"
                errorCode = 1020
                is_pass_check = False
        
        query_result = None

        if is_pass_check:
            query_result = self.metadata_manager.get_path()
            if query_result is None:
                #[TODO]: handle special case: file exist, BUT metadata not found!
                errorMessage = "not_found"
                errorCode = 1020
                is_pass_check = False

        if is_pass_check:
            #self.write(query_result)
            self._downloadData(self.metadata_manager.real_path)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))

    def _downloadData(self, real_path):
        head, tail = os.path.split(real_path)
        self.set_header ('Content-Type', 'application/octet-stream')
        self.set_header ('Content-Disposition', 'attachment; filename='+tail)
        buf_size = 1024 * 200
        with open(real_path, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)
        self.finish()

