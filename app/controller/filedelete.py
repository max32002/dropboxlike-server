#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import tornado.web
from tornado import gen
import logging
import os
import json
from app.controller.meta_manager import MetaManager
from app.dbo.pool import DboPoolSubscriber


class FileDeleteHandler(BaseHandler):
    metadata_manager = None
    to_shared_folder_metadata_array = []

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
                # not allow to do this action.
                errorMessage = "path is empty"
                errorCode = 1013
                is_pass_check = False
                    
        if is_pass_check:
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

            if not self.metadata_manager.real_path is None:
                if not os.path.exists(self.metadata_manager.real_path):
                    # ignore
                    pass
                    # path exist
                    #errorMessage = "path is not exist"
                    #errorCode = 1020
                    #is_pass_check = False
            else:
                errorMessage = "no permission"
                errorCode = 1030
                is_pass_check = False

        if is_pass_check:
            if not self.metadata_manager.can_edit:
                errorMessage = "no write premission"
                errorCode = 1020
                is_pass_check = False

        current_metadata = None
        if is_pass_check:
            current_metadata = self.metadata_manager.get_path()
            if current_metadata is None:
                errorMessage = "metadata not found"
                errorCode = 1021
                is_pass_check = False
        
        

        shared_folder_pool_array = self.metadata_manager.contain_pool_array()
        print "shared_folder_pool_array", shared_folder_pool_array
            
        #errorMessage = "test to breck"
        #errorCode = 1099
        #is_pass_check = False

        if is_pass_check:
            if len(self.metadata_manager.db_path) > 0:
                logging.info('user delete real path at:%s' % (self.metadata_manager.real_path))
                # update metadata in data.
                is_pass_check = self.metadata_manager.delete_metadata(current_metadata=current_metadata)
                if not is_pass_check:
                    errorMessage = "delete metadata fail"
                    errorCode = 1040
                    is_pass_check = False

                if is_pass_check:
                    if os.path.exists(self.metadata_manager.real_path):
                        tornado.ioloop.IOLoop.current().add_callback(self._deletePath,self.metadata_manager.real_path)
            else:
                # shared folder.
                pass

        if is_pass_check:
            if len(shared_folder_pool_array) > 0:
                tornado.ioloop.IOLoop.current().add_callback(self.aferMainDeleteJobDone,shared_folder_pool_array)

        if is_pass_check:
            if not current_metadata is None:
                self.set_header("oid",current_metadata["id"])
                self.write(current_metadata)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
        self.finish()
            
    # [TODO]:
    # delete fail, but file locked.
    @gen.coroutine
    def _deletePath(self, real_path):
        import shutil
        if os.path.exists(real_path):
            if os.path.isfile(real_path):
                try:
                    os.unlink(real_path)
                except Exception as error:
                    errorMessage = "{}".format(error)
                    logging.error(errorMessage)
                    pass
            else:
                for root, dirs, files in os.walk(real_path):
                    yield gen.moment
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                shutil.rmtree(real_path)

    #@gen.coroutine
    def aferMainDeleteJobDone(self, shared_folder_pool_array):
        dbo_pool_sub = DboPoolSubscriber(self.application.sql_client)

        self.to_shared_folder_metadata_array = []
        # start to process shared folder copy.
        for shared_folder_item in shared_folder_pool_array:
            update_poolid = shared_folder_item['poolid']
            pool_ownerid = shared_folder_item['ownerid']
            old_localpoolname = shared_folder_item['poolname']
            to_shared_folder_metadata_manager = MetaManager(self.application.sql_client, self.current_user, old_localpoolname)
            self.to_shared_folder_metadata_array.append(to_shared_folder_metadata_manager)
            
            if pool_ownerid == self.current_user['account']:
                # owner delete
                logging.info('user delete share folder(%d) path at:%s' % (update_poolid, to_shared_folder_metadata_manager.real_path))
                # update metadata in data.
                is_pass_check = to_shared_folder_metadata_manager.delete_metadata()
                if not is_pass_check:
                    errorMessage = "delete metadata fail"
                    errorCode = 1040
                    is_pass_check = False

                if is_pass_check:
                    if os.path.exists(self.metadata_manager.real_path):
                        tornado.ioloop.IOLoop.current().add_callback(self._deletePath,to_shared_folder_metadata_manager.real_path)

                # subscriber delete.
                dbo_pool_sub.delete_pool(update_poolid)
            else:
                # subscriber delete.
                dbo_pool_sub.unscriber(self.current_user['account'], update_poolid)

    