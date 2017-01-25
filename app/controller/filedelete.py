from app.handlers import BaseHandler
import logging
import os
from tornado.options import options

class FileDeleteHandler(BaseHandler):
    def post(self):
        """!create folder file
        @param path file path
        @retval Object http response
        """ 
        path = self.get_argument('path')
        path = path.lstrip('/')

        real_path = None
        is_shared_folder = False

        poolid = self.current_user['poolid']
        self.open_metadata(poolid)

        status_code = 200
        error_dict = None
        status_code, error = self.check_path(path,is_shared_folder)

        # todo:
        # how to handle delete a path that content a shared subfolder.

        if len(path) < 0:
            status_code = 400
            error_dict = dict(error_msg='path is empty.')

        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))
            logging.info('user delete real path at:%s' % (real_path))

        if status_code == 200:
            if not os.path.exists(real_path):
                status_code = 400
                error_dict = dict(error_msg='path is not exist.')

        if status_code == 200:
            # insert log
            # get log info before delete
            action      = 'FileDelete' 
            delta       = 'Delete'
            from_path   = ''
            to_path     = ''
            method      = 'POST'
            is_dir      = 0
            size        = 0

            if os.path.isdir(real_path):
                is_dir  = 1
            if os.path.exists(real_path):
                size    = os.stat(real_path).st_size 

            # start to delete
            # todo:
            #   if delete fail...
            self._deletePath(real_path)

            # todo:
            #   check subfolder content a share folder.

            
            # insert log
            if not os.path.exists(real_path):
                # only path not exist to save.
                self.insert_log(action,delta,path,from_path,to_path,method,is_dir,size)

            # update metadata. (owner)
            self.metadata_manager.remove(path)

            # update metadata. (shared)
            # todo: ...

        else:
            self.set_status(status_code)
            self.write(error_dict)
            # self.write(dict(error=dict(message=errorMessage,code=errorCode)))

    def _deleteThumbnails(self, path):
        if os.path.isfile(real_path):
            # single file
            if thumbnail.isSupportedFormat(path):
                metadata_dic = self.metadata_manager.query(path)
                if 'doc_id' in metadata_dic:
                    doc_id = metadata_dic['doc_id']
                    thumbnail._removeThumbnails(doc_id)
        else:
            # todo:
            # recurcive scan all sub files.
            pass
            
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
