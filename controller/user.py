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

from lib import data_file

class UserListHandler(BaseHandler):
    '''
    Define roles here
    '''
    def has_permission(self, url):
        ans = self.r % 100 == 0
        return ans and super(UserListHandler, self).has_permission(url)

    def get(self):
        users = list(self.db.user.find({'role':{'$in':[b for a,b in self.roles[1:]]}}, sort=[('_id', 1)]))

        role2sys = {b:a for a, b in self.roles}
        for i, user in enumerate(users):
            users[i]['role_str'] = role2sys[user['role']]

        self.render('user-list.html', users=users)

class UserHandler(BaseHandler):
    '''
    Define roles here
    '''
    def has_permission(self, url):
        ans = self.r % 100 == 0
        return ans and super(UserHandler, self).has_permission(url)

    def get(self, uid):
        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else None
        roles = [r for r in self.roles[1:]]
        self.render('user-form.html', user=user, roles=roles)

    def post(self, uid):
        action = self.get_argument('action')
        logging.info('%s do %s to %s' % (self.m, action, uid))

        if action == 'save':
            self.save(uid)
        elif action == 'delete':
            self.delete(uid)

    def delete(self, uid):
        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else {}
        user['valid'] = not user['valid'];
        self.db.user.save(user)
        self.write(dict(ok=1))

    def save(self, uid):
        mail = self.get_argument('mail')
        name = self.get_argument('name')
        pwd = self.get_argument('pwd', '')
        role = self.get_argument('role')
        salt = gen_salt()

        if re.match(r'^([0-9a-zA-Z]([-\.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$', mail) is None:
            self.write(dict(error_msg='invalid mail'))
            return

        #logging.info('uid:%s, mail:%s, pwd:%s, role:%s' % (uid, mail, '***', role))

        user = self.db.user.find_one({'_id': ObjectId(uid)}) if uid else {}
        insert = '_id' not in user

        user.update({
            'mail': mail,
            'name': name,
            'role': int(role),
        })

        if insert:
            plain_pwd = gen_salt()
            pwd = hash_pwd(plain_pwd, mail)

        if pwd:
            user.update({
                'salt':salt,
                'pwd': hash_pwd(pwd, salt),
            })

        if insert:
            user['created_at'] = time.time()
            user['created_by'] = self.m
            user['valid'] = True

        try:
            self.db.user.save(user)

            if insert:
                send_mail(mail,
                    'Your New Account At %s' % self.request.host,
                    'Hi, %s!<br>' % name +
                    'a new accont has been created for you. <br>' +
                    'Username: %s<br>' % mail +
                    'Password: %s<br>' % plain_pwd +
                    'Modify your password once you login. <br>' +
                    'Thanks.',
                    )

            self.write(dict(ok=1))
        except DuplicateKeyError:
            self.write(dict(error_msg='duplicate mail'))

