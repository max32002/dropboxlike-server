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

    def prepare(self):
        uri = self.request.uri
        path = self.request.path
        user = self.current_user

        #logging.info('user:%s is accessing %s', user, uri)

        status_code = 0
        if status_code == 0:
            is_claim_uri = False
            for virtual_folder in options.claim_uri_prefix:
                if path.startswith(virtual_folder):
                    is_claim_uri = True

            if not self.application.claimed:
                # only able to access claim API.
                if not is_claim_uri:
                    # block all access.
                    status_code = 403
            else:
                # claimed.
                if is_claim_uri:
                    # block claim API.
                    status_code = 403

        if status_code == 0:
            if user is None and not self.allow_anony:
                is_ignore_uri = False
                for virtual_folder in options.ignore_token_check_prefix:
                    if path.startswith(virtual_folder):
                        is_ignore_uri = True
                for virtual_folder in options.claim_uri_prefix:
                    if path.startswith(virtual_folder):
                        is_ignore_uri = True

                if not is_ignore_uri:
                    status_code = 401
                    #raise HTTPError(403)
                    #return
                else:
                    # allow anony when auth.
                    pass
        
        if status_code == 0:
            pass
            # pass the premission check.
        else:
            raise HTTPError(status_code)

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

    def check_path(self, path):
        errorMessage = ""
        ret = True

        if path is None:
            errorMessage = "empty_path"
            ret = False
        else:
            if "/../" in path:
                errorMessage = "malformed_path"
                ret = False

            if "//" in path:
                errorMessage = "malformed_path"
                ret = False

            if "\\" in path:
                errorMessage = "malformed_path"
                ret = False

            #Dropbox 的 path pattern
            if path != "":
                import re
                pattern = r'(/(.|[\r\n])*)|(ns:[0-9]+(/.*)?)'
                match_object = re.match(pattern, path)
                if not match_object:
                    errorMessage = "path: '%s' did not match pattern." % (path)
                    ret = False


        return ret, errorMessage

    @property
    def db_account(self):
        my_dbo = DboAccount(self.application.sql_client)
        return my_dbo


class MyErrorHandler(ErrorHandler, BaseHandler):
    """
    Default handler gonna to be used in case of 404 error
    """
    pass
