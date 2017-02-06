#!/usr/bin/env python
#fileencoding=utf-8

import logging

from tornado.web import RequestHandler
from tornado.web import HTTPError
from tornado.web import ErrorHandler
from tornado.options import options

from app.dbo.account import DboAccount

import sqlite3
import os

class BaseHandler(RequestHandler):
    allow_anony = False
    current_user = None

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
                # this is for One server with Many Owner(different home folder).
                if not self.current_user['poolid'] is None:
                    self.user_home = '%s/storagepool/%s' % (options.storage_access_point,self.current_user['poolid'])
        
        if error_code == 0:
            pass
            # pass the premission check.
        else:
            raise HTTPError(error_code)

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


    def has_argument(self, name):
        return name in self.request.arguments

    def write_error(self, status_code, **kwargs):
        if status_code == 403:
            self.write('You do not have previlege to view this page.')
            return
            
        if status_code == 401:
            self.write('Unauthorized.')
            return

        if status_code == 404:
            return

        return super(BaseHandler, self).write_error(status_code, **kwargs)

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
        if self.metadata_manager is None and not poolid is None:
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


class MyErrorHandler(ErrorHandler, BaseHandler):
    """
    Default handler gonna to be used in case of 404 error
    """
    pass
