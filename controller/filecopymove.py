from handlers import BaseHandler
import logging
import os
from tornado.options import options
import shutil

class FileCopyMoveHandler(BaseHandler):
    operation = None
    
    def post(self):
        """!create folder file
        @param path file path
        @retval Object http response
        """ 
        from_path = self.get_argument('from_path')
        from_path = from_path.lstrip('/')
        from_real_path = None
        from_is_shared_folder = False
        to_path = self.get_argument('to_path')
        to_path = to_path.lstrip('/')
        to_real_path = None
        to_is_shared_folder = False

        poolid = self.current_user['poolid']
        self.open_metadata(poolid)

        status_code = 200
        error_dict = None
        status_code, error = self.check_path(from_path,from_is_shared_folder)

        # todo: free space or quota check.
        # // add some code here.

        if status_code == 200:
            status_code, error = self.check_path(to_path,to_is_shared_folder)

        if status_code == 200:
            from_real_path = os.path.abspath(os.path.join(self.user_home, from_path))
            logging.info('user copy real path from:%s' % (from_real_path))
            to_real_path = os.path.abspath(os.path.join(self.user_home, to_path))
            logging.info('user copy real path to:%s' % (to_real_path))

        if status_code == 200:
            if not os.path.exists(from_real_path):
                status_code = 400
                error_dict = dict(error_msg='from_path is not exist.')

        if status_code == 200:
            if os.path.exists(to_real_path):
                status_code = 400
                error_dict = dict(error_msg='to_path is exist.')

        if status_code == 200:
            self._copymove(from_real_path,to_real_path,self.operation)

            # insert log to owner
            action      = self.operation
            delta       = 'Create'
            path        = ''
            #from_path   = ''
            #to_path     = ''
            method      = 'POST'
            is_dir      = 0
            size        = 0

            if os.path.isdir(to_real_path):
                is_dir  = 1
            if os.path.exists(to_real_path):
                size    = os.stat(to_real_path).st_size 
                
            self.insert_log(action,delta,path,from_path,to_path,method,is_dir,size)

            # update metadata. (owner)
            if self.operation is 'FileCopy':
                self.metadata_manager.copy(from_path, to_path, is_dir=is_dir)
            elif self.operation is 'FileMove':
                self.metadata_manager.move(from_path, to_path, is_dir=is_dir)


            # update metadata. (shared)
            # todo: ...
        else:
            self.set_status(status_code)
            self.write(error_dict)

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
            if operation is 'FileCopy':
                shutil.copy(src, dst)
            elif operation is 'FileMove':
                shutil.move(src, dst)
        else:
            # folder to folder copy/move.
            logging.info("%s sub-folder from %s to %s.", operation, src, dst)
            if operation is 'FileCopy':
                self.copyrecursively(src, dst)
            elif operation is 'FileMove':
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
    operation= 'FileCopy'

class FileMoveHandler(FileCopyMoveHandler):
    operation= 'FileMove'
