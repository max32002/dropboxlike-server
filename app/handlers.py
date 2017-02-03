#!/usr/bin/env python
#fileencoding=utf-8

import re
import time
import random
import string
import hashlib
import logging

from tornado.web import RequestHandler
from tornado.web import HTTPError
from tornado.escape import json_decode
from tornado.options import options

from bson.json_util import dumps, loads
from bson.objectid import ObjectId

from app.lib import data_file
from app.lib import utils
from app.dbo.account import DboAccount
from app.dbo.delta import DboDelta

from app.controller.meta_manager import MetaManager
from app.controller.thumbnail_manager import ThumbnailManager

import sqlite3
import os

class BaseHandler(RequestHandler):
    allow_anony = False
    user_home = None
    metadata_manager = None
    thumbnail_manager = None

    def prepare(self):
        uri = self.request.uri
        path = self.request.path
        user = self.current_user

        logging.info('user:%s is accessing %s', user, uri)

        error_code = 0
        if error_code == 0:
            is_claim_uri = False
            for virtual_folder in options.claim_uri_prefix:
                if path.startswith(virtual_folder):
                    is_claim_uri = True

            if not self.application.claimed:
                # only able to access claim API.
                if not is_claim_uri:
                    # block all access.
                    error_code = 403
            else:
                # claimed.
                if is_claim_uri:
                    # block claim API.
                    error_code = 403

        if error_code == 0:
            if user is None and not self.allow_anony:
                is_ignore_uri = False
                for virtual_folder in options.ignore_token_check_prefix:
                    if path.startswith(virtual_folder):
                        is_ignore_uri = True
                for virtual_folder in options.claim_uri_prefix:
                    if path.startswith(virtual_folder):
                        is_ignore_uri = True

                if not is_ignore_uri:
                    error_code = 401
                    #raise HTTPError(403)
                    #return
                else:
                    # allow anony when auth.
                    pass
            else:
                # token valid.
                user_home_poolid = None
                # this is for One server with Many Owner(different home folder).
                self.user_home = '%s/storagepool/%s' % (options.storage_access_point,self.current_user['poolid'])
        
        if error_code == 0:
            pass
            # pass the premission check.
        else:
            raise HTTPError(error_code)

    def get_main_domain(self):
        return self.request.host.split(':')[0]

    def get_current_user(self):
        #[TODO]
        # password change,
        # token expired.
        x_token = self.request.headers.get("Authorization")
        #logging.info('token:%s ', x_token)
        if not x_token is None:
            if len(x_token) > 10 and x_token[:6]=="Token ":
                # trim begin.
                x_token = x_token[6:]
        user_dict = None
        user_account = self.db_account.check_token(x_token)
        if not user_account is None:
            user_dict = {}
            user_dict['account'] = user_account
            user_dict['token'] = x_token
            poolid = self.db_account.get_root_pool(user_account)
            user_dict['poolid'] = poolid

        return user_dict

    def get_share_poolid(self, path):
        account     = self.current_user['account']
        sys_db     = self.db_account
        is_cross_owner_pool = False
        if len(path) > 0:
            is_cross_owner_pool, delta_poolid = sys_db.find_share_poolid(account, path)
            logging.info("share delta_poolid: %s ... path: %s", delta_poolid, path)
        return is_cross_owner_pool, delta_poolid

    def insert_log(self,    action,
                            delta       = 'Create',
                            path        = '',
                            from_path   = '',
                            to_path     = '',
                            method      = 'POST',
                            is_dir      = 0,
                            size        = 0
                            ):

        account     = self.current_user['account']
        update_time = utils.get_timestamp()
        delta_poolid = self.current_user['poolid']

        if not delta_poolid is None:
            delta_db_path = '%s/history/%s/delta.db' % (options.storage_access_point,delta_poolid)
            logging.info("owner delta_poolid: %s ... ", delta_poolid)
            delta_conn = sqlite3.connect(delta_db_path)
            dbo_delta = DboDelta(delta_conn)
            dbo_delta.save_log(action,delta,path,from_path,to_path,account,update_time,method,is_dir,size)

        # duplicate log for share folder.
        # todo:
        # path need convert to relative with share folder local path.
        if len(path) > 0:
            # single path.
            # todo:
            #   need handle delete parent event.
            is_cross_owner_pool, share_delta_poolid = self.get_share_poolid(path)
            if not share_delta_poolid is None:
                delta_db_path = '%s/history/%s/delta.db' % (options.storage_access_point,share_delta_poolid)
                delta_conn = sqlite3.connect(delta_db_path)
                dbo_delta = DboDelta(delta_conn)
                dbo_delta.save_log(action,delta,path,from_path,to_path,account,update_time,method,is_dir,size)
        
        if len(from_path) > 0 and len(to_path) >0:
            # double path.
            # (case 1) for copy event, add files.
            # (case 2) for move event, from_path and to_path not same pool, do delete / add files event.
            # (case 3) for move event, from_path and to_path not same pool, do mvoe files event.
            is_cross_owner_pool, from_share_delta_poolid = self.get_share_poolid(from_path)
            is_cross_owner_pool, to_share_delta_poolid = self.get_share_poolid(to_path)
            
            # (case 1 & case 2)
            action      = 'UploadFile'
            delta       = 'Create'
            
            # (case 2)
            action      = 'FileDelete'
            delta       = 'Delete'
            
            # (case 3)
            # directly by pass owner event.
            pass


    def has_argument(self, name):
        return name in self.request.arguments

    def write_error(self, status_code, **kwargs):
        if status_code == 403:
            self.write('You do not have previlege to view this page.')
            return

        if status_code == 401:
            self.write('Unauthorized.')
            return

        return super(BaseHandler, self).write_error(status_code, **kwargs)

    def is_ajax_request(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def dumps(self, obj):
        return dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)

    def loads(self, s):
        return loads(s)

    def render(self, template, **kwargs):
        #kwargs['site'] = 'Shire'
        return super(BaseHandler, self).render(template, **kwargs)

    def check_path(self, path, is_shared_folder):
        status_code = 200
        error_dict = None

        if self.user_home is None:
            status_code = 400
            error_dict = dict(error_msg='user is not valid.')
        if "/../" in path:
            status_code = 400
            error_dict = dict(error_msg='path is not valid.')

        # there are some invalid symbol should not appear on path, is need to check.
        # to do some check here.

        if status_code == 200:
            real_path = os.path.abspath(os.path.join(self.user_home, path))

            # if not is shared folder.
            if not is_shared_folder:
                if not real_path.startswith(self.user_home):
                    status_code = 400
                    error_dict = dict(error_msg='path is not valid.')

        return status_code, error_dict

    def open_metadata(self, poolid):
        account = self.current_user['account']
        if self.metadata_manager is None:
            # open database.
            db_path = '%s/metadata/%s/metadata.db' % (options.storage_access_point,poolid)
            #logging.info("owner metadata poolid: %s ... ", db_path)
            client = sqlite3.connect(db_path)
            self.metadata_manager = MetaManager(client,account)

    def open_thumbnail(self):
        if self.thumbnail_manager is None:
            # open thumbnail database
            db_path = '%s/thumbnails/thumbnail.db' % (options.storage_access_point)
            logging.info("thumbnail db: %s ... ", db_path)
            client = sqlite3.connect(db_path)
            self.thumbnail_manager = ThumbnailManager(client)

    @property
    def db_account(self):
        my_dbo = DboAccount(self.application.sql_client)
        return my_dbo

    @property
    def db_pool(self):
        my_dbo = DboAccount(self.application.sql_client)
        return my_dbo

    @property
    def db_delta(self):
        my_dbo = None
        if self.user_delta_db is not None:
            logging.info("connecting to user delta database %s ...", self.user_delta_db)
            client = sqlite3.connect(sys_db)
            my_dbo = DboDelta(client)
        return my_dbo


#################################################################
## User Administration

def gen_salt():
    return ''.join(random.choice(string.letters) for i in xrange(16))

def hash_pwd(pwd, salt):
    return hashlib.sha1(pwd+'|'+salt).hexdigest()[:16]

