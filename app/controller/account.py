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

from bson.json_util import dumps, loads
from bson.objectid import ObjectId

from lib import data_file

class AccountHandler(BaseHandler):
    def get(self):
        user = self.db.user.find_one({'mail':self.m})
        assert user is not None

        role2sys = {b:a for a, b in self.roles}
        user['role_str'] = role2sys[user['role']] if user['role'] in role2sys else ''

        self.render('account.html', user=user)

    def post(self):
        user = self.db.user.find_one({'mail':self.m})
        assert user is not None

        name = self.get_argument('name')
        cpwd = self.get_argument('cpwd')
        npwd = self.get_argument('npwd')
        salt = gen_salt()

        if hash_pwd(cpwd, user['salt']) != user['pwd']:
            self.write(dict(error_msg='current password not correct.'))
            return

        user.update({
            'name': name,
            'pwd': hash_pwd(npwd, salt),
            'salt': salt,
        })
        self.db.user.save(user)
        self.write(dict(ok=1))

class SigninHandler(BaseHandler):
    allow_anony = True

    def get(self):
        if self.current_user is not None:
            self.redirect(self.get_next_url(self.current_user['role']))
            return

        self.render('signin.html')

    def post(self):
        mail = self.get_argument('mail')
        pwd = self.get_argument('pwd')

        user = self.db.user.find_one({'mail': mail})
        if user is None:
            self.write(dict(error_msg='user not exist.'))
            return
        if hash_pwd(pwd, user['salt']) != user['pwd']:
            self.write(dict(error_msg='password incorrect.'))
            return

        if not user['valid']:
            self.write(dict(error_msg='account banned.'))
            return

        user['last_login_time'] = time.time()
        self.db.user.save(user)

        cookie_user = {
            'email': mail,
            'role': user['role'],
            'login_sn': gen_salt(),
        }
        self.set_secure_cookie(
            "user",
            self.dumps(cookie_user),
            expires_days=7,
            domain=self.get_main_domain()
        )
        self.set_cookie(
            "login_sn",
            cookie_user['login_sn'],
            domain=self.get_main_domain()
        )

        self.write(dict(url=self.get_next_url(user['role'])))

    def get_next_url(self, role):
        referer = self.request.headers.get('Referer')
        if referer and referer != self.request.full_url():
            return referer

        return '/'

class SignoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user', domain=self.get_main_domain())
        self.clear_cookie('login_sn', domain=self.get_main_domain())
        self.redirect(self.request.headers.get('Referer', '/'))
