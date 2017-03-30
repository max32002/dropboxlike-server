#!/usr/bin/env python
#encoding=utf-8

from app.handlers import BaseHandler
import uuid
import logging
import json
from app.lib import utils

class AuthHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        auth_dbo = self.db_account

        #logging.info('body:%s' % (self.request.body))
        _body = None
        is_pass_check = False
        errorMessage = ""
        errorCode = 0

        if not auth_dbo is None:
            is_pass_check = True
        else:
            errorMessage = "database return null"
            errorCode = 1001
            is_pass_check = False

        if is_pass_check:
            try :
                _body = json.loads(self.request.body)
                is_pass_check = True
            except Exception:
                errorMessage = "wrong json format"
                errorCode = 1002
                pass

        account = None
        password = None
        if is_pass_check:
            is_pass_check = False
            #logging.info('%s' % (str(_body)))
            if _body:
                try :
                    if 'account' in _body:
                        account = _body['account'][:100]
                    if 'password' in _body:
                        password = _body['password'][:100]
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1003

        if is_pass_check:
            if account is None:
                errorMessage = "account empty"
                errorCode = 1010
                is_pass_check = False
            else:
                if len(account)<4:
                    errorMessage = "account too short"
                    errorCode = 1011
                    is_pass_check = False

            if password is None:
                errorMessage = "password empty"
                errorCode = 1012
                is_pass_check = False
            else:
                if len(password)<4:
                    errorMessage = "password too short"
                    errorCode = 1013
                    is_pass_check = False

        # TODO: need a log to avoid bruce-force attach here.
                    
        if is_pass_check:
            is_pass_check = auth_dbo.login(account, password)
            if not is_pass_check:
                errorMessage = "password incorrect."
                errorCode = 1020

        if is_pass_check:
            token = utils.get_token()
            while auth_dbo.pk_exist(token):
                token = utils.get_token()

            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip

            #logging.info('token:%s, account:%s, password:%s, remote_ip:%s' % (token, account, password, remote_ip))
            auth_dbo.save_token(token,account,remote_ip)
            ret_dict = {'access_token': token, 'account':account}
            self.write(ret_dict)
            #self.render('auth.json', token=token, account=account)
        else:
            self.set_status(401)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))
            #self.render('auth_fail.json', account='u12345')
