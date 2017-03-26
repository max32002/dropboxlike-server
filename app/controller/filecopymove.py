#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import tornado.web
from tornado import gen
import logging
import os
import json
import shutil
from app.dbo.pool import DboPoolSubscriber
from app.controller.meta_manager import MetaManager

class FileCopyMoveHandler(BaseHandler):
    from_metadata_manager = None
    to_metadata_manager = None
    to_shared_folder_metadata_array = []
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
        autorename = False

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
                errorMessage = "duplicated_or_nested_paths"
                errorCode = 1014
                is_pass_check = False
                    
        if is_pass_check:
            self.from_metadata_manager = MetaManager(self.application.sql_client, self.current_user, from_path)

            if not self.from_metadata_manager.real_path is None:
                if not os.path.exists(self.from_metadata_manager.real_path):
                    # [TODO]:
                    # create real folders from database.
                    #pass
                    # path not exist
                    errorMessage = "from_path:%s is not exist" % (from_path,)
                    errorCode = 1020
                    is_pass_check = False
            else:
                errorMessage = "no permission"
                errorCode = 1030
                is_pass_check = False
    
        if is_pass_check:
            self.to_metadata_manager = MetaManager(self.application.sql_client, self.current_user, to_path)

            if not self.to_metadata_manager.real_path is None:
                if os.path.exists(self.to_metadata_manager.real_path):
                    # [TODO]:
                    # apply autorenename rule.
                    #pass
                    # path exist
                    if not autorename:
                        errorMessage = "conflict"
                        errorCode = 1021
                        is_pass_check = False
                    else:
                        # start auto rename
                        pass
            else:
                errorMessage = "no permission"
                errorCode = 1030
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

        from_shared_folder_pool_array = self.from_metadata_manager.contain_pool_array()
        #print "from_shared_folder_pool_array", from_shared_folder_pool_array
        #self.application.sql_client.isolation_level = None
        if is_pass_check:
            # rename shared folder under from_path
            if self.operation is self.OPERATION_MOVE:
                if len(from_shared_folder_pool_array) > 0:
                    is_pass_check = False
                    if not self.to_metadata_manager.poolname is None:
                        if len(self.to_metadata_manager.poolname) == 0:
                            # ONLY is allowed in this case.
                            is_pass_check = True
                    else:
                        # unkonw error
                        pass

                    if not is_pass_check:
                        errorMessage = "unable to move share folder under share folder"
                        errorCode = 1026
                        print errorMessage, errorCode

        # PS: need roolback, don't move variable into sub block.
        dbo_pool_sub = DboPoolSubscriber(self.application.sql_client)
        if self.operation is self.OPERATION_MOVE:
            if is_pass_check:
                user_account = self.current_user['account']

                for shared_folder_item in from_shared_folder_pool_array:
                    update_poolid = shared_folder_item['poolid']
                    old_localpoolname = shared_folder_item['poolname']
                    new_localpoolname = to_path + old_localpoolname[len(from_path):]
                    #print "from [%s] to [%s]" % (shared_folder_item['poolname'], new_localpoolname)
                    dbo_pool_sub.update_localpoolname(user_account, update_poolid, new_localpoolname, autocommit=False)

        if is_pass_check:
            logging.info('%s real path from:%s' % (self.operation, self.from_metadata_manager.real_path))
            logging.info('%s real path to:%s' % (self.operation, self.to_metadata_manager.real_path))
            
            # update metadata. (owner)
            if self.operation is self.OPERATION_COPY:
                if len(self.from_metadata_manager.db_path) > 0:
                    is_pass_check, current_metadata, errorMessage = self.to_metadata_manager.copy_metadata(self.from_metadata_manager.poolid, self.from_metadata_manager.db_path)
                    if current_metadata is None:
                        errorMessage = "metadata not found"
                        errorCode = 1040
                        is_pass_check = False
                else:
                    # shared folder root
                    pass
                current_metadata = self.to_metadata_manager.get_path()

                #self.to_metadata_manager.copy(from_path, to_path, is_dir=is_dir)
            if self.operation is self.OPERATION_MOVE:
                if len(self.from_metadata_manager.db_path) > 0:
                    is_pass_check, current_metadata, errorMessage = self.to_metadata_manager.move_metadata(self.from_metadata_manager.poolid, self.from_metadata_manager.db_path)
                    if current_metadata is None:
                        errorMessage = "metadata not found"
                        errorCode = 1040
                        is_pass_check = False
                else:
                    # shared folder root
                    pass
                current_metadata = self.to_metadata_manager.get_path()

        if self.operation is self.OPERATION_MOVE:
            if is_pass_check:
                # make sure all things are correct, start to write to database.
                dbo_pool_sub.conn.commit()
            else:
                dbo_pool_sub.conn.rollback()

        if is_pass_check:
            # must everyday is done, thus to move files.
            #self._copymove(self.from_metadata_manager.real_path,self.to_metadata_manager.real_path,self.operation)
            if not current_metadata is None:
                if self.operation is self.OPERATION_COPY:
                    tornado.ioloop.IOLoop.current().add_callback(self._copymove, self.from_metadata_manager.real_path, self.to_metadata_manager.real_path, self.operation, self.to_metadata_manager.add_thumbnail, current_metadata, True, from_path, to_path, from_shared_folder_pool_array)
                    #tornado.ioloop.IOLoop.current().spawn_callback(self._copymove, self.from_metadata_manager.real_path, self.to_metadata_manager.real_path, self.operation, self.to_metadata_manager.add_thumbnail, current_metadata, True, from_path, to_path, from_shared_folder_pool_array)

                if self.operation is self.OPERATION_MOVE:
                    if len(self.from_metadata_manager.db_path) > 0:
                        tornado.ioloop.IOLoop.current().add_callback(self._copymove, self.from_metadata_manager.real_path, self.to_metadata_manager.real_path, self.operation, self.to_metadata_manager.add_thumbnail, current_metadata, False, None, None, None)
                        #tornado.ioloop.IOLoop.current().spawn_callback(self._copymove, self.from_metadata_manager.real_path, self.to_metadata_manager.real_path, self.operation, self.to_metadata_manager.add_thumbnail, current_metadata, False, None, None, None)
                    else:
                        # shared folder root
                        pass

        if is_pass_check:
            if not current_metadata is None:
                self.set_header("oid",current_metadata["id"])
                self.write(current_metadata)
                logging.info(current_metadata)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
        self.finish()

    #@gen.coroutine
    def aferMainCopyJobDone(self, from_path, to_path, from_shared_folder_pool_array):
        self.to_shared_folder_metadata_array = []
        # start to process shared folder copy.
        for shared_folder_item in from_shared_folder_pool_array:
            update_poolid = shared_folder_item['poolid']
            old_localpoolname = shared_folder_item['poolname']
            new_localpoolname = to_path + old_localpoolname[len(from_path):]
            from_shared_folder_metadata_manager = MetaManager(self.application.sql_client, self.current_user, old_localpoolname)
            to_shared_folder_metadata_manager = MetaManager(self.application.sql_client, self.current_user, new_localpoolname)
            self.to_shared_folder_metadata_array.append(to_shared_folder_metadata_manager)
            is_pass_check, copy_shared_folder_metadata, errorMessage = to_shared_folder_metadata_manager.copy_metadata(update_poolid, "")
            if is_pass_check and not copy_shared_folder_metadata is None:
                #tornado.ioloop.IOLoop.current().add_callback(self._copymove,from_shared_folder_metadata_manager.real_path, to_shared_folder_metadata_manager.real_path, self.OPERATION_COPY, to_shared_folder_metadata_manager.add_thumbnail, copy_shared_folder_metadata, False, None, None, None)
                #tornado.ioloop.IOLoop.current().spawn_callback(self._copymove,from_shared_folder_metadata_manager.real_path, to_shared_folder_metadata_manager.real_path, self.OPERATION_COPY, to_shared_folder_metadata_manager.add_thumbnail, copy_shared_folder_metadata, False, None, None, None)
                self._copymove(from_shared_folder_metadata_manager.real_path, to_shared_folder_metadata_manager.real_path, self.OPERATION_COPY, to_shared_folder_metadata_manager.add_thumbnail, copy_shared_folder_metadata, False, None, None, None)
                

    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

    #@gen.coroutine
    def _copymove(self, src, dst, operation, thumbnail_callback, current_metadata, is_call_shared_folder_job, from_path, to_path, from_shared_folder_pool_array):
        #yield gen.moment
        if os.path.isfile(src):
            # file to file copy/move
            head, tail = os.path.split(dst)
            self._createFolder(head)
            if operation is self.OPERATION_COPY:
                shutil.copy(src, dst)
                # no matter file or folder should scan sub-folder.
                #tornado.ioloop.IOLoop.current().add_callback(thumbnail_callback,current_metadata)
                #tornado.ioloop.IOLoop.current().spawn_callback(thumbnail_callback,current_metadata)
                thumbnail_callback(current_metadata)
            elif operation is self.OPERATION_MOVE:
                shutil.move(src, dst)
        else:
            # folder to folder copy/move.
            #logging.info("%s sub-folder from %s to %s.", operation, src, dst)
            if operation is self.OPERATION_COPY:
                self.copyrecursively(src, dst)
                # no matter file or folder should scan sub-folder.
                #tornado.ioloop.IOLoop.current().add_callback(thumbnail_callback,current_metadata)
                #tornado.ioloop.IOLoop.current().spawn_callback(thumbnail_callback,current_metadata)
                thumbnail_callback(current_metadata)
                
                if is_call_shared_folder_job:
                    if not from_shared_folder_pool_array is None:
                        if len(from_shared_folder_pool_array) > 0:
                            #tornado.ioloop.IOLoop.instance().add_callback(self.aferMainCopyJobDone,from_path, to_path, from_shared_folder_pool_array)
                            self.aferMainCopyJobDone(from_path, to_path, from_shared_folder_pool_array)
            elif operation is self.OPERATION_MOVE:
                shutil.move(src, dst)

    def copyrecursively(self, root_src_dir, root_target_dir):
        logging.info("copy from %s to %s.", root_src_dir, root_target_dir)
        for src_dir, dirs, files in os.walk(root_src_dir):
            db_path = os.path.abspath(src_dir)[len(os.path.abspath(root_src_dir))+1:]
            #print "db_path", db_path
            #dst_dir = src_dir.replace(root_src_dir, root_target_dir)
            dst_dir = os.path.join(root_target_dir, db_path)
            #print "dst_dir", dst_dir
            if not os.path.exists(dst_dir):
                self._createFolder(dst_dir)

            files = [self.decodeName(f) for f in files]
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                if os.path.exists(src_file):
                    shutil.copy(src_file, dst_dir)
                else:
                    logging.error(src_file)

    def decodeName(self, name):
        if type(name) == str: # leave unicode ones alone
            try:
                name = name.decode('utf8')
            except:
                name = name.decode('windows-1252')
        return name

class FileCopyHandler(FileCopyMoveHandler):
    operation= FileCopyMoveHandler.OPERATION_COPY

class FileMoveHandler(FileCopyMoveHandler):
    operation= FileCopyMoveHandler.OPERATION_MOVE
