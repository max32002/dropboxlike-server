#!/usr/bin/env python
#encoding=utf-8
from app.handlers import BaseHandler
import logging
from app.controller.meta_manager import MetaManager
import json
import os

class MetadataHandler(BaseHandler):
    mode = 'FILE'
    metadata_manager = None

    def post(self):
        self.set_header('Content-Type','application/json')

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        _body = None
        if is_pass_check:
            #logging.info('%s' % (str(self.request.body)))
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
            if path == "/":
                #PS: dropbox not all path='/''
                path = ""

            ret, errorMessage = self.check_path(path)
            if not ret:
                is_pass_check = False
                errorCode = 1010

        if self.mode == "FILE":
            if is_pass_check:
                if len(path)==0:
                    errorMessage = "path is empty"
                    errorCode = 1011
                    is_pass_check = False

        if is_pass_check:
            #logging.info('path %s' % (path))
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

            if not self.metadata_manager.real_path is None:
                if not os.path.exists(self.metadata_manager.real_path):
                    pass
                    #[TODO]: rebuild path on server side from database?
                    #errorMessage = "path on server not found"
                    #errorCode = 1020
                    #is_pass_check = False

        query_result = None
        if is_pass_check:
            # start to get metadata (owner)
            if self.mode == "FILE":
                query_result = self.metadata_manager.get_path()
            else:
                folder_id = 0
                current_metadata = self.metadata_manager.get_path()
                if not current_metadata is None:
                    folder_id = current_metadata["id"]
                self.set_header("oid", folder_id)

                query_result = self.metadata_manager.list_folder(show_share_folder=True)

            if query_result is None:
                errorMessage = "metadata not found"
                errorCode = 1021
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

class ListFolderHandler(MetadataHandler):
    mode = 'FOLDER'

