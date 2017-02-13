#!/usr/bin/env python
#fileencoding=utf-8

from app.handlers import BaseHandler
import logging
from app.lib import data_file
from app.lib import misc
from app.lib import utils
from tornado.options import options
import json
from app.controller.meta_manager import MetaManager
from app.dbo.chunk_upload import DboChunkUpload
import os
from stat import *


class UploadSessionHandler(BaseHandler):
    action = None
    dbo_chunk_upload = None

    def new_session_id(self):
        import uuid
        session_id = str(uuid.uuid4().hex)
        while self.dbo_chunk_upload.pk_exist(session_id):
            session_id = str(uuid.uuid4().hex)
        ret, errorMessage = self.dbo_chunk_upload.session_start(session_id,self.current_user['account'])
        if not ret:
            #[TODO]: session_id conflict.
            #errorMessage = "not able to get session_id from database."
            session_id = None

        return session_id

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

        session_id = None
        offset = 0

        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'cursor' in _body:
                        cursor = _body['cursor']
                        if 'session_id' in cursor:
                            session_id = cursor['session_id']
                        if 'offset' in cursor:
                            offset = cursor['offset']
                    if 'commit' in _body:
                        commit = _body['commit']
                        if 'path' in commit:
                            path = commit['path']
                        if 'mode' in commit:
                            mode = commit['mode']
                        if 'autorename' in commit:
                            autorename = commit['autorename']
                        if 'client_modified' in commit:
                            client_modified = commit['client_modified']
                        if 'mute' in commit:
                            mute = commit['mute']
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1002

        self.dbo_chunk_upload = DboChunkUpload(self.application.sql_client)

        if self.action == "SessionFinish":
            if is_pass_check:
                ret, errorMessage = self.check_path(path)
                if not ret:
                    is_pass_check = False
                    errorCode = 1010

            if is_pass_check:
                if len(path)==0:
                    errorMessage = "path is empty"
                    errorCode = 1011
                    is_pass_check = False

            if is_pass_check:
                self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

        if self.action == "SessionAppend" or self.action == "SessionFinish":
            if is_pass_check:
                if session_id is None:
                    errorMessage = "session_id is empty"
                    errorCode = 1012
                    is_pass_check = False

            if is_pass_check:
                if len(session_id)==0:
                    errorMessage = "session_id is empty"
                    errorCode = 1012
                    is_pass_check = False

            if is_pass_check:
                if offset is None:
                    errorMessage = "offset is empty"
                    errorCode = 1013
                    is_pass_check = False
        else:
            #if self.action == "SessionStart":
            session_id = self.new_session_id()
            offset = 0
            if session_id is None:
                errorMessage = "not able to get session_id from database."
                errorCode = 1012
                is_pass_check = False

        if is_pass_check:
            if not self.dbo_chunk_upload.pk_exist(session_id):
                errorMessage = "session_id expire or not exist"
                errorCode = 1013
                is_pass_check = False
        
        session_real_path = None
        if is_pass_check:
            session_real_path = '%s/upload_session/%s' % (options.storage_access_point,session_id)
            logging.info('Upload to real path at:%s' % (session_real_path))

            if self.action == "SessionAppend" or self.action == "SessionFinish":
                if not os.path.exists(session_real_path):
                    errorMessage = "temp file for this session_id has lost"
                    errorCode = 1015
                    is_pass_check = False

        if is_pass_check:
            #print "offset", offset
            is_pass_check, errorMessage = self._write_offset(session_real_path, self.request.body, offset)
            if not is_pass_check:
                errorCode = 1012

        if self.action == "SessionFinish":
            if is_pass_check:
                if os.path.exists(self.metadata_manager.real_path):
                    # [TODO]: to Overwrite(with new revision) or autorename

                    # need implement a revision feature.
                    # need move target to versions folder.
                    os.unlink(self.metadata_manager.real_path)

                import shutil
                shutil.move(session_real_path, self.metadata_manager.real_path)

                is_pass_check = self.dbo_chunk_upload.pk_delete(session_id)
                if not is_pass_check:
                    errorMessage = "remove upload session info fail."
                    errorCode = 1020

            if is_pass_check:
                # update metadata. (owner)
                if os.path.exists(self.metadata_manager.real_path):
                    is_pass_check, errorMessage = self._updateMtimeToFile(self.metadata_manager.real_path, client_modified)
                    if not is_pass_check:
                        errorCode = 1022

                    size=os.stat(self.metadata_manager.real_path).st_size
                    #print "size",size
                    rev=None
                    content_hash=misc.md5_file(self.metadata_manager.real_path)
                    #print "content_hash",content_hash

                    is_pass_check, query_result, errorMessage = self.metadata_manager.add_metadata(size=size, content_hash=content_hash, client_modified=client_modified)

        

        # start to output.
        query_result = {"session_id": session_id}
        if self.action == "SessionFinish":
            if is_pass_check:
                query_result = self.metadata_manager.get_path()
                if query_result is None:
                    errorMessage = "add metadata in database fail"
                    errorCode = 1023
                    is_pass_check = False

        if is_pass_check:
            if not query_result is None:
                self.write(query_result)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))


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
            os.utime(real_path, (atime,client_modified))
            is_pass_check = True
        except Exception as error:
            errorMessage = "{}".format(error)
            logging.error(errorMessage)
            pass
        return is_pass_check, errorMessage

    def _createFolder(self, directory_name):
        if not os.path.exists(directory_name):
            try:
                os.makedirs(directory_name)
            except OSError as exc: 
                pass

    def _write_offset(self,real_path,data,offset):
        # force create folder
        ret = False
        errorMessage = ""
        mode = "r+b"
        if offset == 0:
            mode = "wb"

        head, tail = os.path.split(real_path)
        self._createFolder(head)
        try:
            f = open(real_path, mode)
            f.seek(offset)
            f.write(data)
            f.close()
            ret = True
        #except IOError as error:
        except Exception as error:
            errorMessage = "{}".format(error)
            logging.error(errorMessage)
            pass
        return ret, errorMessage

class UploadSessionStartHandler(UploadSessionHandler):
    action = 'SessionStart'

class UploadSessionAppendHandler(UploadSessionHandler):
    action = 'SessionAppend'


class UploadSessionFinishHandler(UploadSessionHandler):
    action = 'SessionFinish'

