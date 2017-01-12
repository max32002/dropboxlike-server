from app.handlers import BaseHandler
import logging
import os
from tornado.options import options
from app.controller.meta_manager import MetaManager


class FileCreateFolderHandler(BaseHandler):

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

        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))
            logging.info('user create real path at:%s' % (real_path))

        if status_code == 200:
            if os.path.exists(real_path):
                status_code = 400
                error_dict = dict(error_msg='path is exist.')

        if status_code == 200:
            self._createFolder(real_path)

            # insert log
            action      = 'CreateFolder' 
            delta       = 'Create'
            from_path   = ''
            to_path     = ''
            method      = 'POST'
            is_dir      = 0
            size        = 0

            if os.path.isdir(real_path):
                is_dir  = 1
            if os.path.exists(real_path):
                size    = os.stat(real_path).st_size 
                
            self.insert_log(action,delta,path,from_path,to_path,method,is_dir,size)

            # update metadata. (owner)
            self.metadata_manager.add(path,is_dir=1)

            query_result = self.metadata_manager.query(path)
            if not query_result is None:
                self.write(query_result)
        else:
            self.set_status(status_code)
            self.write(error_dict)

    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

