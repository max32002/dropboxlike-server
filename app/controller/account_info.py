from app.handlers import BaseHandler
from tornado.options import options
import logging
from app.lib import utils

from app.controller.meta_manager import MetaManager

class AccountUsageHandler(BaseHandler):
    ''' Acount Info API Controller'''
    metadata_manager = None

    def post(self):
        self.set_header('Content-Type','application/json')

        is_pass_check = True
        errorMessage = ""
        errorCode = 0

        used = 0
        if is_pass_check:
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, "")
            used = self.metadata_manager.count_usage()

        allocated = self.get_free_space(options.storage_access_point)


        if is_pass_check:
            self.set_status(200)
            dict_usage = {'used': used,'trash': 0, 'allocated': allocated}
            self.write(dict_usage)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))

    def get_free_space(self, path):
        import os
        s = os.statvfs(path)
        f = (s.f_bavail * s.f_frsize) / 1024
        return f

class AccountSecurityQuestionHandler(BaseHandler):
    ''' Acount Security Question API Controller'''

    def post(self):
        self.set_header('Content-Type','application/json')
        auth_dbo = self.db_account

        errorMessage = ""
        errorCode = 0

        #logging.info('body:%s' % (self.request.body))
        is_pass_check = False
        
        _body = None
        if is_pass_check:
            is_pass_check = False
            try :
                _body = json.loads(self.request.body)
                is_pass_check = True
            except Exception:
                #raise BadRequestError('Wrong JSON', 3009)
                errorMessage = "wrong json format"
                errorCode = 1001
                pass

        question = None
        answer = None
        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    if 'question' in _body:
                        question = _body['question'][:256]
                    if 'answer' in _body:
                        answer = _body['answer'][:256]
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1002
                    pass

        if is_pass_check:
            if question is None:
                errorMessage = "question is empty"
                errorCode = 1003
                is_pass_check = False
            else:
                if len(question) == 0:
                    errorMessage = "question is empty"
                    errorCode = 1004
                    is_pass_check = False

            if answer is None:
                errorMessage = "answer is empty"
                errorCode = 1005
                is_pass_check = False
                if len(question) == 0:
                    errorMessage = "answer is empty"
                    errorCode = 1005
                    is_pass_check = False

        if is_pass_check:
            account = self.current_user['account']
            auth_dbo.security_update(account, question, answer)
    
        if is_pass_check:
            # every thing is correct
            self.set_status(200)
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #self.render('auth_fail.json', account='u12345')
