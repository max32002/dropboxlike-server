from handlers import BaseHandler
import logging
import json
from lib import utils
from dbo.drive import DboDrive
from dbo.pincode import DboPincode
from dbo.pincode import DboPincodeLog

class DriveClaimAuthHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        drive_dbo = DboDrive(self.application.sql_client)
        pincode_dbo = DboPincode(self.application.sql_client)
        pincode_log_dbo = DboPincodeLog(self.application.sql_client)

        errorMessage = ""
        errorCode = 0

        #logging.info('body:%s' % (self.request.body))
        is_pass_check = False
        
        if not drive_dbo is None:
            is_pass_check = True
        else:
            errorMessage = "database return null"
            errorCode = 1001
            is_pass_check = False

        if is_pass_check:
            if not pincode_dbo is None:
                is_pass_check = True
            else:
                errorMessage = "database return null"
                errorCode = 1002
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
                errorCode = 1003
                pass

        pincode = None
        password = None
        request_id = None
        client_md5 = None
        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    if 'pincode' in _body:
                        pincode = _body['pincode'][:10]
                    if 'password' in _body:
                        password = _body['password'][:20]
                    if 'request_id' in _body:
                        request_id = _body['request_id']
                    if 'client_md5' in _body:
                        client_md5 = _body['client_md5'][:64]
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1004
                    pass

        if is_pass_check:
            if pincode is None:
                errorMessage = "PinCode empty"
                errorCode = 1010
                is_pass_check = False
            if password is None:
                errorMessage = "Password empty"
                errorCode = 1011
                is_pass_check = False
            if request_id is None:
                errorMessage = "request_id empty"
                errorCode = 1012
                is_pass_check = False
            if client_md5 is None:
                errorMessage = "client_md5 empty"
                errorCode = 1013
                is_pass_check = False

        if is_pass_check:
            # [TODO]: Password brute-force attack.
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
            log_ret, log_dict = pincode_log_dbo.add(pincode,password,request_id,client_md5,remote_ip)
            #print "log_ret", log_ret
            if not log_ret:
                errorMessage = "claim_auth log fail"
                errorCode = 1020
                is_pass_check = False
                # insert log fail.

            # check pincode & password
            
            #logging.info('token:%s, account:%s, password:%s, remote_ip:%s' % (token, account, password, remote_ip))

        # check poken on public server.
        pincode_dict = None
        if is_pass_check:
            pincode_dict = pincode_dbo.match(pincode,password)
            #print "pincode_dict", pincode_dict
            if pincode_dict is None:
                errorMessage = "Password not match"
                errorCode = 1021
                is_pass_check = False

        if is_pass_check:
            # last step
            sn = pincode_dict['sn']
            print "sn", sn
            
        if is_pass_check:
            # every thing is correct
            pass
        else:
            self.set_status(400)
            self.write(dict(error_msg=errorMessage,error_code=errorCode))
            #self.render('auth_fail.json', account='u12345')
