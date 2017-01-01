from handlers import BaseHandler
import logging
import json
from lib import utils

class DriveClaimHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        drive_dbo = DboDrive(self.application.sql_client)
        pincode_dbo = DboDrive(self.application.sql_client)

        errorMessage = ""
        errorCode = 0

        #logging.info('body:%s' % (self.request.body))
        is_pass_check = False
        
        if not drive_dbo is None:
            is_pass_check = True
        else:
            errorMessage = "database return null"
            errorCode = 101
            is_pass_check = False

        if is_pass_check:
            if not pincode_dbo is None:
                is_pass_check = True
            else:
                errorMessage = "database return null"
                errorCode = 101
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
                errorCode = 102
                pass

        pincode = None
        password = None
        poken = None
        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    pincode = _body['pincode']
                    password = _body['password']
                    poken = _body['poken']
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 103
                    pass

        if is_pass_check:
            if pincode is None:
                errorMessage = "pincode empty"
                errorCode = 104
                is_pass_check = False
            if password is None:
                errorMessage = "password empty"
                errorCode = 104
                is_pass_check = False
            if poken is None:
                errorMessage = "poken empty"
                errorCode = 104
                is_pass_check = False

        if is_pass_check:
            # [TODO]: Password brute-force attack.
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip

            # check pincode & password
            
            #logging.info('token:%s, account:%s, password:%s, remote_ip:%s' % (token, account, password, remote_ip))
            # check poken on public server.

            self.set_header('X-Subject-Token',token)
            auth_db.save_token(token,account,remote_ip)
            self.render('auth.json', token=token, account=account)
        else:
            self.set_status(400)
            self.write(dict(error_msg=errorMessage,error_code=errorCode))
            #self.render('auth_fail.json', account='u12345')
