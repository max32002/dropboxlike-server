from handlers import BaseHandler
import uuid
import logging
import json
from lib import utils

class AuthHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        auth_db = self.db_account

        #logging.info('body:%s' % (self.request.body))
        _body = None
        is_pass_check = False
        try :
            _body = json.loads(self.request.body)
            is_pass_check = True
        except Exception:
            #raise BadRequestError('Wrong JSON', 3009)
            pass

        account = None
        password = None
        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    account = _body['account']
                    password = _body['password']
                    is_pass_check = True
                except Exception:
                    pass
                    
        if is_pass_check:
            if account is not None and password is not None:
                is_pass_check = auth_db.login(account, password)

        if is_pass_check:
            token = utils.get_token()
            while auth_db.pk_exist(token)==1:
                token = str(uuid.uuid4().hex)

            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip

            #logging.info('token:%s, account:%s, password:%s, remote_ip:%s' % (token, account, password, remote_ip))
            self.set_header('X-Subject-Token',token)
            auth_db.save_token(token,account,remote_ip)
            self.render('auth.json', token=token, account=account)
        else:
            self.set_status(401)
            self.write(dict(error_msg='password incorrect.',error_code=123))
            #self.render('auth_fail.json', account='u12345')
