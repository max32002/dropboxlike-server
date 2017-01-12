from app.handlers import BaseHandler
import logging
import os
from tornado.options import options
from app.lib import data_file
import uuid
import sqlite3
from app.lib import utils
import shutil
from app.dbo.chunk_upload import DboChunkUpload

class FilesHandler(BaseHandler):
    action = None
    dbo_chunk_upload = None

    def get(self, path):
        """!download file
        @param path file path
        @retval Object http response
        """ 

        path = path.lstrip('/')
        real_path = None
        is_shared_folder = False

        poolid = self.current_user['poolid']
        self.open_metadata(poolid)

        status_code = 200
        error_dict = None
        status_code, error = self.check_path(path,is_shared_folder)

        if len(path) < 0:
            status_code = 400
            error_dict = dict(error_msg='path is empty.')
        
        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))
            logging.info('user downlaod path:%s' % (real_path))

        if status_code == 200:
            if not os.path.exists(real_path):
                status_code = 400
                error_dict = dict(error_msg='path is not exist.')
            else:
                # path exist.
                if not os.path.isfile(real_path):
                    status_code = 400
                    error_dict = dict(error_msg='path is not file.')

        # Check permission
        # todo: ...

        if status_code == 200:
            # todo: response correct mtime.
            # ...

            self._downloadData(real_path)
        else:
            self.set_status(status_code)
            self.write(error_dict)

    def _downloadData(self, real_path):
        head, tail = os.path.split(real_path)
        self.set_header ('Content-Type', 'application/octet-stream')
        self.set_header ('Content-Disposition', 'attachment; filename='+tail)
        buf_size = 1024 * 200
        with open(real_path, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)
        self.finish()

    def put(self, path):
        """!upload file
        @param path file path
        @retval Object http response
        """ 
        return self.post(path)

    def post(self, path):
        """!upload file
        @param path file path
        @retval Object http response
        """ 

        # todo: free space or quota check.
        # // add some code here.

        # Check permission
        # todo: ...
                
        x_mtime = self.request.headers.get("X-Meta-FC-Mtime")
        if not '#' in x_mtime:
            # format error...
            x_mtime = ''

        x_filesize = 0
        req_filesize = self.request.headers.get("X-File-Size")
        if not req_filesize is None:
            x_filesize = int(req_filesize)
        
        offset = 0
        if self.has_argument('offset'):
            offset = int(self.get_argument('offset'))

        upload_id = None
        if self.has_argument('upload_id'):
            upload_id = self.get_argument('upload_id')

        # need access database.
        poolid = self.current_user['poolid']
        self.open_metadata(poolid)
        self.open_thumbnail()

        path = path.lstrip('/')
        real_path = None
        is_shared_folder = False

        status_code = 200
        error_dict = None
        status_code, error = self.check_path(path,is_shared_folder)

        if len(path) < 0:
            status_code = 400
            error_dict = dict(error_msg='path is empty.')

        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))
            logging.info('user upload path:%s' % (real_path))

        if status_code == 200:
            # path exist and is a FOLDER!
            if os.path.isdir(real_path):
                status_code = 400
                error_dict = dict(error_msg='path is a folder, unable to overwrite.')

        if status_code == 200:
            if self.action == 'ChunkUpload':
                if upload_id is None and offset > 0:
                    status_code = 400
                    error_dict = dict(error_msg='upload_id is required.')

        # update chunk_upload database. (owner or shared both?)
        #dbo_chunk_upload = None

        if status_code == 200:
            if self.action == 'ChunkUpload' or self.action == 'CommitUpload':
                chunk_upload_db_path = '%s/chunk_upload/%s/chunk_upload.db' % (options.storage_access_point,poolid)
                #logging.info("chunk_upload poolid: %s ... ", poolid)
                chunk_upload_conn = sqlite3.connect(chunk_upload_db_path)
                self.dbo_chunk_upload = DboChunkUpload(chunk_upload_conn)
                

            if self.action == 'ChunkUpload':
                # save to database, and get upload_id
                if upload_id is None:
                    upload_id = str(uuid.uuid4().hex)
                    while self.dbo_chunk_upload.pk_exist(upload_id)==1:
                        upload_id = str(uuid.uuid4().hex)
                    self.dbo_chunk_upload.save(upload_id,path,x_filesize,offset,x_mtime,utils.get_timestamp(),self.current_user['account'])
                else:
                    # update current offset to database.
                    # todo: or not necessary to do...
                    pass

                # chunk upload
                if not upload_id is None:
                    chunk_upload_real_path = '%s/chunk_upload/%s/%s' % (options.storage_access_point,poolid,upload_id)
                    self._write_offset(chunk_upload_real_path, self.request.body, offset)
                else:
                    # error! upload_id empty.
                    pass
                self.write(dict(upload_id=upload_id,offset=offset+len(self.request.body)))
                

            if self.action == 'CommitUpload':
                # commit upload, load info from database, write to file.
                if not upload_id is None:
                    chunk_upload_real_path = '%s/chunk_upload/%s/%s' % (options.storage_access_point,poolid,upload_id)
                    self._check_revision(poolid, path, real_path)
                    shutil.move(chunk_upload_real_path, real_path)

                    # load x_mtime from database (if client only upload mtime at first time.)
                    #x_mtime = ...

                    self._commit_upload(path, real_path, x_mtime)
                    self.dbo_chunk_upload.pk_delete(upload_id)
                else:
                    # error! upload_id empty.
                    pass

            if self.action is None:
                # normal upload
                self._check_revision(poolid, path, real_path)
                self._commit_upload(path, real_path, x_mtime)

        else:
            self.set_status(status_code)
            self.write(error_dict)

    def _write_offset(self,real_path,data,offset):
        # force create folder
        head, tail = os.path.split(real_path)
        self._createFolder(head)

        try:
            f = open(real_path,'wb')
            f.seek(offset)
            f.write(data)
            f.close()
        except IOError:
            pass

    def _check_revision(self, poolid, path, real_path):
        if os.path.isfile(real_path):
            # need implement a revision feature.
            # todo: ...
            # need move target to versions folder.
            os.unlink(real_path)

            # remove ALL thumbnails before delete metadata.
            self.thumbnail_manager.remove(path)

            # remove database from metadata, and insert new to revision.
            self.metadata_manager.remove(path)

    def _commit_upload(self, path, real_path, x_mtime):
        # force create folder
        head, tail = os.path.split(real_path)
        self._createFolder(head)

        # start to upload
        self._uploadData(real_path, x_mtime)

        # insert log
        action      = 'UploadFile' 
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

        # create new thumbnail
        self.thumbnail_manager.add(real_path)

        # update metadata. (owner)
        poolid = self.current_user['poolid']
        self.open_metadata(poolid)
        out_dic = self.metadata_manager.add(path, bytes=size, rev='1', mtime=x_mtime, is_dir=0)

        commit_dict = {
    "size": str(size),
    "rev": "",
    "thumb_exists": False,
    "bytes": size,
    "modified": utils.get_timestamp(),
    "path": path,
    "is_dir": False,
    "icon": "",
    "root": "",
    "mime_type": "",
    "revision": 1
}
       #self.write(commit_dict)
    
    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

    def _uploadData(self, real_path, x_mtime):
        result = 0
        try:
            f_data = self.request.body
            f_url = data_file.save(real_path, f_data)
            logging.info('upload finished -------%s' % (f_url))
            self._updateMtimeToFile(real_path,x_mtime)

            result = 1
        except Exception as error:
            #raise MyError('connection break')
            logging.info("Error: {}".format(error))
        return result

    def _updateMtimeToFile(self, real_path, x_mtime):
        # update access and modify time.
        if len(x_mtime) > 0 and "#" in x_mtime:
            #<Modified time#Created time#Accessed time>
            tmp_mtime = x_mtime.split('#')
            #access / modify time.
            times = (int(tmp_mtime[2])/1000.0, int(tmp_mtime[0])/1000.0)
            os.utime(real_path, times)
            #logging.info('new times -------%s' % (times))



class ChunkUploadHandler(FilesHandler):
    action = 'ChunkUpload'

class CommitUploadHandler(FilesHandler):
    action = 'CommitUpload'

