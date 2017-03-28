#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
from app.dbo.temp_link import DboTempLink
from app.controller.meta_manager import MetaManager
import logging
import json
import os
from app.lib import utils
from tornado.options import options
import datetime
from app.dbo.metadata import DboMetadata
import sqlite3
from tornado.web import StaticFileHandler
import tornado.gen
from tornado import httputil
import mimetypes
import stat
from tornado import iostream

class GetTempLinkHandler(BaseHandler):

    def post(self):
        #self.set_header('Content-Type','application/json')

        dbo_temp_link = DboTempLink(self.application.sql_client)

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

        if is_pass_check:
            if len(path)==0:
                errorMessage = "path is empty"
                errorCode = 1011
                is_pass_check = False

        if is_pass_check:
            #logging.info('path %s' % (path))
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

            if not self.metadata_manager.real_path is None:
                if not os.path.isfile(self.metadata_manager.real_path):
                    errorMessage = "path on server not found"
                    errorCode = 1020
                    is_pass_check = False

        query_result = None
        if is_pass_check:
            query_result = self.metadata_manager.get_path()
            if query_result is None:
                errorMessage = "metadata not found"
                errorCode = 1021
                is_pass_check = False

        temp_link = None
        if is_pass_check:
            temp_link = "%ss-%s-%s" % (utils.get_token(),query_result['content_hash'],utils.get_token())
            while dbo_temp_link.pk_exist(temp_link):
                temp_link = "%ss-%-%s" % (utils.get_token(),query_result['content_hash'],utils.get_token())
            ret = False
            for i in range(3):
                # may conflict...
                ret = dbo_temp_link.add(temp_link,self.metadata_manager.poolid,query_result['id'],query_result['content_hash'],self.current_user['account'])
                if ret:
                    break
            if not ret:
                errorMessage = "add temp_link into database fail."
                errorCode = 1022
                is_pass_check = False


        ret_dict = {'metadata':query_result, 'link': temp_link, 'port':options.streaming_port}
        self.set_header('Content-Type','application/json')
        if is_pass_check:
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))

class ViewTempLinkHandler(BaseHandler):
    #remark by max, tornado's bug, I can't fix, the connection unable to finish.
    #@tornado.gen.coroutine
    #def head(self, link_id):
        #return self.view_link(link_id, include_body=False)

    #@tornado.gen.coroutine
    def get(self, link_id):
        return self.view_link(link_id, include_body=True)

    @tornado.gen.coroutine
    def view_link(self, link_id, include_body=True):
        dbo_temp_link = DboTempLink(self.application.sql_client)

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        TEMPLINK_EXPIRY_SECONDS = 4 * 60 * 60   # 4 hours.

        #logging.info("link_id:%s" % (link_id))
        if is_pass_check:
            if len(link_id)!=99:
                errorMessage = "temp link is wrong"
                errorCode = 1010
                is_pass_check = False

        temp_link_dict = None
        if is_pass_check:
            #logging.info('path %s' % (path))
            temp_link_dict = dbo_temp_link.pk_query(link_id)
            createdTime = temp_link_dict['createdTime']
            time_db = datetime.datetime.strptime(createdTime, "%Y-%m-%d %H:%M:%S")
            #utc_datetime = datetime.datetime.now()
            utc_datetime = datetime.datetime.utcnow()
            time_diff = (utc_datetime - time_db).total_seconds()
            #print 'past: %d seconds, %d seconds is our limit' % (time_diff, TEMPLINK_EXPIRY_SECONDS)
            if time_diff > TEMPLINK_EXPIRY_SECONDS:
                errorMessage = "temp link expire"
                errorCode = 1012
                is_pass_check = False

        real_path = None
        if is_pass_check:
            dbo_metadata = None
            metadata_dict = None

            poolid = temp_link_dict['poolid']
            doc_id = temp_link_dict['doc_id']
            content_hash_old = temp_link_dict['content_hash']
            metadata_conn = self.open_metadata_db(poolid)
            dbo_metadata = DboMetadata(metadata_conn)
            metadata_dict = dbo_metadata.pk_query(doc_id)
            if not metadata_dict is None:
                if metadata_dict['content_hash'] != content_hash_old:
                    errorMessage = "file content changed"
                    errorCode = 1013
                    is_pass_check = False

                real_path = u'%s/storagepool/%s%s' % (options.storage_access_point, poolid, metadata_dict['path'])

        if is_pass_check:
            if not os.path.isfile(real_path):
                errorMessage = "file not exist"
                errorCode = 1014
                is_pass_check = False

        if is_pass_check:
            #print "real_path", real_path
            #self.start_stream(real_path, include_body)
            self.absolute_path = os.path.abspath(real_path)
            self.modified = self.get_modified_time()
            self.set_headers()

            request_range = None
            range_header = self.request.headers.get("Range")
            if range_header:
                # As per RFC 2616 14.16, if an invalid Range header is specified,
                # the request will be treated as if the header didn't exist.
                request_range = httputil._parse_request_range(range_header)

            size = self.get_content_size()
            if request_range:
                start, end = request_range
                if (start is not None and start >= size) or end == 0:
                    # As per RFC 2616 14.35.1, a range is not satisfiable only: if
                    # the first requested byte is equal to or greater than the
                    # content, or when a suffix with length 0 is specified
                    self.set_status(416)  # Range Not Satisfiable
                    self.set_header("Content-Type", "text/plain")
                    self.set_header("Content-Range", "bytes */%s" % (size, ))
                    return
                if start is not None and start < 0:
                    start += size
                if end is not None and end > size:
                    # Clients sometimes blindly use a large range to limit their
                    # download size; cap the endpoint at the actual file size.
                    end = size
                # Note: only return HTTP 206 if less than the entire range has been
                # requested. Not only is this semantically correct, but Chrome
                # refuses to play audio if it gets an HTTP 206 in response to
                # ``Range: bytes=0-``.
                if size != (end or size) - (start or 0):
                    self.set_status(206)  # Partial Content
                    self.set_header("Content-Range", httputil._get_content_range(start, end, size))
            else:
                start = end = None

            if start is not None and end is not None:
                content_length = end - start
            elif end is not None:
                content_length = end
            elif start is not None:
                content_length = size - start
            else:
                content_length = size
            self.set_header("Content-Length", content_length)
            
            if include_body:
                content = self.get_content(self.absolute_path, start, end)
                if isinstance(content, bytes):
                    content = [content]
                for chunk in content:
                    try:
                        self.write(chunk)
                        yield self.flush()
                    except iostream.StreamClosedError:
                        #print "StreamClosedError"
                        return
            else:
                pass
                #assert self.request.method == "HEAD"

        else:
            if errorCode == 1012:
                self.set_status(410)
            else:
                if errorCode == 1013:
                    self.set_status(304)
                else:
                    self.set_header('Content-Type','application/json')
                    self.set_status(400)
                    self.write(dict(error=dict(message=errorMessage,code=errorCode)))
                    logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
            

    def start_stream(self, real_path, include_body=True):
        pass


    def set_headers(self):
        """Sets the content and caching headers on the response.

        .. versionadded:: 3.1
        """
        self.set_header("Accept-Ranges", "bytes")

        if self.modified is not None:
            self.set_header("Last-Modified", self.modified)

        content_type = self.get_content_type()
        if content_type:
            self.set_header("Content-Type", content_type)

    @classmethod
    def get_content(cls, abspath, start=None, end=None):
        with open(abspath, "rb") as file:
            if start is not None:
                file.seek(start)
            if end is not None:
                remaining = end - (start or 0)
            else:
                remaining = None
            while True:
                chunk_size = 64 * 1024
                if remaining is not None and remaining < chunk_size:
                    chunk_size = remaining
                chunk = file.read(chunk_size)
                if chunk:
                    if remaining is not None:
                        remaining -= len(chunk)
                    yield chunk
                else:
                    if remaining is not None:
                        assert remaining == 0
                    return

    def _stat(self):
        if not hasattr(self, '_stat_result'):
            self._stat_result = os.stat(self.absolute_path)
        return self._stat_result

    def get_content_size(self):
        """Retrieve the total size of the resource at the given path.

        This method may be overridden by subclasses.

        .. versionadded:: 3.1

        .. versionchanged:: 4.0
           This method is now always called, instead of only when
           partial results are requested.
        """
        stat_result = self._stat()
        return stat_result[stat.ST_SIZE]

    def get_modified_time(self):
        stat_result = self._stat()
        modified = datetime.datetime.utcfromtimestamp(
            stat_result[stat.ST_MTIME])
        return modified

    def get_content_type(self):
        mime_type, encoding = mimetypes.guess_type(self.absolute_path)
        return mime_type

    # open database.
    #[TODO] multi-database solution.
    #def open_metadata(self, poolid):
    def get_metadata_db_path(self, poolid):
        db_path = u'%s/metadata.db' % (options.storage_access_point)
        #logging.info("open metadata poolid: %s ... ", db_path)
        return db_path


    # open database.
    #[TODO] multi-database solution.
    #def open_metadata(self, poolid):
    def open_metadata_db(self, poolid):
        #if not poolid is None:
            #db_path = '%s/metadata/%s/metadata.db' % (options.storage_access_point,poolid)
            #logging.info("owner metadata poolid: %s ... ", db_path)
            #client = sqlite3.connect(db_path)
        db_path = self.get_metadata_db_path(poolid)
        client = sqlite3.connect(db_path)
        return client




