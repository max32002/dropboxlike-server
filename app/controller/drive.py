from app.handlers import BaseHandler
import logging
import json
from tornado.options import options
from app.lib import libHttp
from app.lib import utils
from app.lib import misc
from app.dbo.drive import DboDrive
from app.dbo.pincode import DboPincode
from app.dbo.pincode import DboPincodeLog

class DriveClaimAuthHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        drive_dbo = DboDrive(self.application.sql_client)
        pincode_dbo = DboPincode(self.application.sql_client)
        pincode_log_dbo = DboPincodeLog(self.application.sql_client)
        auth_dbo = self.db_account

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
        drive_title = ""
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
                    if 'drive_title' in _body:
                        drive_title = _body['drive_title'][:256]
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
            else:
                if len(pincode)<4:
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

            if drive_title is None:
                errorMessage = "drive_title empty"
                errorCode = 1014
                is_pass_check = False
            else:
                if len(drive_title)==0:
                    errorMessage = "drive_title empty"
                    errorCode = 1014
                    is_pass_check = False

        if is_pass_check:
            # [TODO]: Password brute-force attack.
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
            log_ret = pincode_log_dbo.add(pincode,password,request_id,client_md5,remote_ip)
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

        ret_dict = {}
        if is_pass_check:
            # last step
            is_owner=1
            ret,user_account,user_password = auth_dbo.new_user(is_owner)
            #print "new user:",ret,account,password
            account_info = "%s,%s" % (user_account,user_password)
            ret_dict['account'] = user_account
            ret_dict['password'] = user_password
            #account_info_encrypt = misc.aes_encrypt(password,account_info)
            #print "account_info:",account_info
            #print "account_info_encrypt:",account_info_encrypt

            # start check on public server.
            confirm_result = False

            http_code,json_obj = self.call_drive_confirm_api(pincode_dict, request_id, client_md5, drive_title)
            if http_code > 0:
                if http_code == 200 and not json_obj is None:
                    #print "json:", json_obj
                    pincode = json_obj.get('pincode','')
                    drive_token = json_obj.get('drive_token','')
                    account_sn = json_obj.get('account_sn','')

                    ret_dict['pincode'] = pincode
                    ret_dict['account_sn'] = account_sn

                    drive_dbo.empty()
                    is_pass_check = drive_dbo.add(drive_title, drive_token)

                if http_code >= 400 and http_code <= 403 and not json_obj is None:
                    # by pass the error message
                    is_pass_check = False
                    error_json = json_obj.get('error',None)
                    if not error_json is None:
                        errorMessage = error_json.get('message','')
                        errorCode = error_json.get('code',0)

                    # auto pooling, after get pincode.
                    # for short-pincode & changeable & GUI support sultion.
                    #drive_query(drive_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
            else:
                #print "server is not able be connected or cancel by user"
                pass

            if not confirm_result:
                # delete create new user.
                auth_dbo.pk_delete(user_account)

            
        if is_pass_check:
            # every thing is correct
            self.set_status(200)
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error_msg=errorMessage,error_code=errorCode))
            #self.render('auth_fail.json', account='u12345')

    def call_drive_confirm_api(self, pincode_dict, request_id, client_md5, drive_title):
        api_reg_pattern = "1/drive/claim_confirm"
        #api_hostname = "claim.dropboxlike.com"
        api_hostname = "127.0.0.1"
        api_url = "https://%s/%s" % (api_hostname,api_reg_pattern)

        confirm_dict = self.prepare_confirm_json_body()
        confirm_dict['sn'] = pincode_dict['sn']
        confirm_dict['pincode'] = pincode_dict['pincode']
        confirm_dict['request_id'] = request_id
        confirm_dict['client_md5'] = client_md5
        confirm_dict['drive_title'] = drive_title
        json_body = json.dumps(confirm_dict)
        #print "json_body", json_body

        http_obj = libHttp.Http()
        (new_html_string, http_code) = http_obj.get_http_response_core(api_url, data=json_body)
        json_obj = None
        if http_code>=200 and http_code <= 403:
            # direct read the string to json.
            try :
                json_obj = json.loads(new_html_string)
            except Exception, err:
                # not is json format.
                pass
        else:
            #print "server return error code: %d" % (http_code,)
            pass
            # error
        return http_code,json_obj


    def prepare_confirm_json_body(self):
        import socket
        computerName = socket.gethostname()
        localIp = socket.gethostbyname(socket.gethostname())

        from uuid import getnode as get_mac
        mac = get_mac()
        mac_formated = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

        node_number = 0

        data = {'localIp':localIp, 'port':options.port, 'mac': mac_formated, 'client_version':options.versionCode}
        return data