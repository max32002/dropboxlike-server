#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import logging
from tornado import gen
import json
from app.controller.meta_manager import MetaManager
from app.lib import thumbnail
import os

class DownloadHandler(BaseHandler):
    mode = "FILE"
    metadata_manager = None

    def get(self):
        self.post()

    #@gen.coroutine
    def post(self):
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
        format = None
        size = "w64h64"
        start = None
        length =  None
        rev = None
        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'path' in _body:
                        path = _body['path']
                    if 'start' in _body:
                        start = _body['start']
                    if 'length' in _body:
                        length = _body['length']
                    if 'rev' in _body:
                        rev = _body['rev']

                    # for thumbnail.
                    if 'format' in _body:
                        format = _body['format']
                    if 'size' in _body:
                        size = _body['size']

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
            logging.info('download %s from real path at:%s' % (self.mode, self.metadata_manager.real_path))

            if not self.metadata_manager.real_path is None:
                if not os.path.exists(self.metadata_manager.real_path):
                    errorMessage = "not_found"
                    errorCode = 1020
                    is_pass_check = False
            else:
                errorMessage = "no permission"
                errorCode = 1030
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
            head, filename = os.path.split(self.metadata_manager.real_path)
            download_path = self.metadata_manager.real_path
            if self.mode == "THUMBNAIL":
                doc_id = query_result['id']
                download_path = thumbnail._getThumbnailPath(doc_id, size, os.path.splitext(filename)[-1])

            is_pass_check = self._downloadData(download_path, filename)
            if not is_pass_check:
                for i in range(0):
                    logging.info("waiting thumbnail file to ready(%d): %s ... " % (i, download_path))
                    #yield gen.sleep(2)
                    is_pass_check = self._downloadData(download_path, filename)
                    if is_pass_check:
                        break

            if not is_pass_check:
                errorMessage = "file not found"
                errorCode = 1030
                is_pass_check = False

        if is_pass_check:
            pass
        else:
            self.set_header('Content-Type','application/json')
            if errorCode != 1030:
                self.set_status(400)
            else:
                # only this case return 404.
                self.set_status(404)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
        self.finish()

    def _downloadData(self, real_path, filename):
        ret = False
        
        logging.info("download real file: %s ... " % (real_path))
        if os.path.isfile(real_path):
            with open(real_path, 'rb') as f:
                buf_size = 1024 * 200
                self.set_header ('Content-Type', 'application/octet-stream')
                self.set_header ('Content-Disposition', 'attachment; filename='+filename)
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    self.write(data)
                ret = True
        return ret
            

class ThumbnailHandler(DownloadHandler):
    mode = "THUMBNAIL"
