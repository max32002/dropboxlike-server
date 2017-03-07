#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import tornado.web
import logging
import os
import json
import shutil
from app.controller.meta_manager import MetaManager

class FileCopyMoveHandler(BaseHandler):
    from_metadata_manager = None
    to_metadata_manager = None
    operation = None
    OPERATION_COPY = "FileCopy"
    OPERATION_MOVE = "FileMove"

    @tornado.web.asynchronous
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

        from_path = None
        to_path = None
        allow_shared_folder = None
        autorename = None

        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'from_path' in _body:
                        from_path = _body['from_path']
                    if 'to_path' in _body:
                        to_path = _body['to_path']
                    if 'allow_shared_folder' in _body:
                        allow_shared_folder = _body['allow_shared_folder']
                    if 'autorename' in _body:
                        autorename = _body['autorename']
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1002

        if is_pass_check:
            ret, errorMessage = self.check_path(from_path)
            if not ret:
                is_pass_check = False
                errorCode = 1010

        if is_pass_check:
            if len(from_path)==0:
                errorMessage = "from_path is empty"
                errorCode = 1011
                is_pass_check = False

        if is_pass_check:
            ret, errorMessage = self.check_path(to_path)
            if not ret:
                is_pass_check = False
                errorCode = 1012

        if is_pass_check:
            if len(to_path)==0:
                errorMessage = "to_path is empty"
                errorCode = 1013
                is_pass_check = False

        if is_pass_check:
            if to_path == from_path:
                errorMessage = "conflict"
                errorCode = 1014
                is_pass_check = False
                
        if is_pass_check:
            if to_path.startswith(from_path):
                errorMessage = "conflict"
                errorCode = 1014
                is_pass_check = False
                    
        if is_pass_check:
            self.from_metadata_manager = MetaManager(self.application.sql_client, self.current_user, from_path)

            if not os.path.exists(self.from_metadata_manager.real_path):
                # [TODO]:
                # create real folders from database.
                #pass
                # path not exist
                errorMessage = "from_path:%s is not exist" % (from_path,)
                errorCode = 1020
                is_pass_check = False

        if is_pass_check:
            self.to_metadata_manager = MetaManager(self.application.sql_client, self.current_user, to_path)

            if os.path.exists(self.to_metadata_manager.real_path):
                # [TODO]:
                # apply autorenename rule.
                #pass
                # path exist
                errorMessage = "to_path is not exist"
                errorCode = 1021
                is_pass_check = False

        if is_pass_check:
            if not self.to_metadata_manager.can_edit:
                errorMessage = "to_path no write permission"
                errorCode = 1022
                is_pass_check = False

        if is_pass_check:
            if self.operation is self.OPERATION_MOVE:                
                if not self.from_metadata_manager.can_edit:
                    errorMessage = "from_path no write permission"
                    errorCode = 1023
                    is_pass_check = False

        query_result = None
        if is_pass_check:
            query_result = self.from_metadata_manager.get_path()
            if query_result is None:
                errorMessage = "from_path metadata not found"
                errorCode = 1024
                is_pass_check = False

        # handle special case: when database & storage is not synced!
        # real file deleted on server, but metadata exist.
        # for now, just delete server side metadata.
        current_metadata = None
        if is_pass_check:
            current_metadata = self.to_metadata_manager.get_path()
            if not current_metadata is None:
                # delete to_path metadata.
                is_pass_check = self.to_metadata_manager.delete_metadata()
                if not is_pass_check:
                    errorMessage = "delete to_path metadata in database fail"
                    errorCode = 1025
                    is_pass_check = False

        if is_pass_check:
            logging.info('%s real path from:%s' % (self.operation, self.from_metadata_manager.real_path))
            logging.info('%s real path to:%s' % (self.operation, self.to_metadata_manager.real_path))
            
            # update metadata. (owner)
            if self.operation is self.OPERATION_COPY:
                is_pass_check, current_metadata, errorMessage = self.to_metadata_manager.copy_metadata(self.from_metadata_manager.poolid, self.from_metadata_manager.db_path)
                if current_metadata is None:
                    errorMessage = "metadata not found"
                    errorCode = 1040
                    is_pass_check = False

                #self.to_metadata_manager.copy(from_path, to_path, is_dir=is_dir)
            if self.operation is self.OPERATION_MOVE:
                is_pass_check, current_metadata, errorMessage = self.to_metadata_manager.move_metadata(self.from_metadata_manager.poolid, self.from_metadata_manager.db_path)
                if current_metadata is None:
                    errorMessage = "metadata not found"
                    errorCode = 1040
                    is_pass_check = False

        if is_pass_check:
            # [TODO]:
            # rename shared folder under from_path
            pass

        if is_pass_check:
            # must everyday is done, thus to move files.
            #self._copymove(self.from_metadata_manager.real_path,self.to_metadata_manager.real_path,self.operation)
            tornado.ioloop.IOLoop.instance().add_callback(self._copymove,self.from_metadata_manager.real_path,self.to_metadata_manager.real_path,self.operation)


        if is_pass_check:
            if not current_metadata is None:
                self.set_header("oid",current_metadata["id"])
                self.write(current_metadata)
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

    def _copymove(self, src, dst, operation):
        if os.path.isfile(src):
            # file to file copy/move
            head, tail = os.path.split(dst)
            self._createFolder(head)
            if operation is self.OPERATION_COPY:
                shutil.copy(src, dst)
            elif operation is self.OPERATION_MOVE:
                shutil.move(src, dst)
        else:
            # folder to folder copy/move.
            #logging.info("%s sub-folder from %s to %s.", operation, src, dst)
            if operation is self.OPERATION_COPY:
                self.copyrecursively(src, dst)
            elif operation is self.OPERATION_MOVE:
                shutil.move(src, dst)

    def copyrecursively(self, root_src_dir, root_target_dir):
        for src_dir, dirs, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_target_dir)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.copy(src_file, dst_dir)


class FileCopyHandler(FileCopyMoveHandler):
    operation= FileCopyMoveHandler.OPERATION_COPY

class FileMoveHandler(FileCopyMoveHandler):
    operation= FileCopyMoveHandler.OPERATION_MOVE
