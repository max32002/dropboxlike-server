#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import tornado.web
import logging
from app.lib import data_file
from app.lib import utils
import json
from app.controller.meta_manager import MetaManager
import os
from stat import *

class UploadHandler(BaseHandler):
    metadata_manager = None

    @tornado.web.asynchronous
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
        mode = None
        autorename = None
        client_modified = None
        mute = None
        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'path' in _body:
                        path = _body['path']
                    if 'mode' in _body:
                        mode = _body['mode']
                    if 'autorename' in _body:
                        autorename = _body['autorename']
                    if 'client_modified' in _body:
                        client_modified = _body['client_modified']
                    if 'mute' in _body:
                        mute = _body['mute']
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
            if not self.metadata_manager.can_edit:
                errorMessage = "no write premission"
                errorCode = 1020
                is_pass_check = False

        if is_pass_check:
            logging.info(u'Upload to real path at:%s' % (self.metadata_manager.real_path))
            is_pass_check = self._saveFile(self.metadata_manager.real_path, self.request.body)

            # update metadata. (owner)
            if not self.metadata_manager.real_path is None:
                if os.path.isfile(self.metadata_manager.real_path):
                    if not client_modified is None:
                        is_pass_check, errorMessage = self._updateMtimeToFile(self.metadata_manager.real_path, client_modified)
                        if not is_pass_check:
                            errorCode = 1022
                else:
                    errorMessage = "save file to server fail"
                    errorCode = 1023
            else:
                errorMessage = "no permission"
                errorCode = 1030
                is_pass_check = False

        query_result = None
        if is_pass_check:
            is_pass_check, query_result, errorMessage = self.metadata_manager.add_metadata_from_file()
            if not is_pass_check:
                errorMessage = "add metadata in database fail"
                errorCode = 1024

        if is_pass_check:
            self.write(query_result)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
        self.finish()

    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

    def _updateMtimeToFile(self, real_path, client_modified):
        # update access and modify time.
        #<Modified time#Created time#Accessed time>
        is_pass_check = False
        errorMessage = ""
        try :
            # update modify time.
            #st = os.stat(real_path)
            #atime = st[ST_ATIME]
            atime = utils.get_timestamp()
            if client_modified is None:
                client_modified = atime
            os.utime(real_path, (atime,client_modified))
            is_pass_check = True
        except Exception as error:
            errorMessage = "{}".format(error)
            logging.error(errorMessage)
            pass
        return is_pass_check, errorMessage


    def _saveFile(self, real_path, f_data):
        parent_node, item_name = os.path.split(real_path)
        # ensure parent exist.
        self._createFolder(parent_node)

        #f_type = path.splitext(path)[-1]
        ret, message = data_file.save(real_path, f_data)

        return ret
