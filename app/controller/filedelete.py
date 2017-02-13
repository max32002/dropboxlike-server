from app.handlers import BaseHandler
import logging
import os
import json
from tornado.options import options
from app.controller.meta_manager import MetaManager

class FileDeleteHandler(BaseHandler):
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

            if not os.path.exists(self.metadata_manager.real_path):
                # ignore
                pass
                # path exist
                #errorMessage = "path is not exist"
                #errorCode = 1020
                #is_pass_check = False

        if is_pass_check:
            if not self.metadata_manager.can_edit:
                errorMessage = "no write premission"
                errorCode = 1020
                is_pass_check = False

        query_result = None
        if is_pass_check:
            query_result = self.metadata_manager.get_path()
            if query_result is None:
                errorMessage = "metadata not found"
                errorCode = 1021
                is_pass_check = False

        if is_pass_check:
            logging.info('user delete real path at:%s' % (self.metadata_manager.real_path))
            if os.path.exists(self.metadata_manager.real_path):
                self._deletePath(self.metadata_manager.real_path)

            # update metadata in data.
            is_pass_check = self.metadata_manager.delete_metadata()
            if not is_pass_check:
                errorMessage = "delete metadata fail"
                errorCode = 1030
                is_pass_check = False


        if is_pass_check:
            self.write(query_result)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))


    def _deleteThumbnails(self, path):
        if os.path.isfile(real_path):
            # single file
            if thumbnail.isSupportedFormat(path):
                metadata_dic = self.metadata_manager.query(path)
                if 'doc_id' in metadata_dic:
                    doc_id = metadata_dic['doc_id']
                    thumbnail._removeThumbnails(doc_id)
        else:
            # [TODO]:
            # recurcive scan all sub files.
            pass
            
    # [TODO]:
    # delete fail, but file locked.
    def _deletePath(self, real_path):
        import shutil

        if os.path.isfile(real_path):
            os.unlink(real_path)
        else:
            for root, dirs, files in os.walk(real_path):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
            shutil.rmtree(real_path)
