from app.handlers import BaseHandler
import logging
import json
from tornado.options import options
from app.dbo.repo import DboRepo

class RepoSecurityUpdateHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        auth_dbo = self.db_account

        errorMessage = ""
        errorCode = 0

        #logging.info('body:%s' % (self.request.body))
        is_pass_check = False
        
        if not auth_dbo is None:
            is_pass_check = True
        else:
            errorMessage = "database return null"
            errorCode = 1001
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
                    errorCode = 1004
                    pass

        if is_pass_check:
            if question is None:
                errorMessage = "question empty"
                errorCode = 1010
                is_pass_check = False
            else:
                if len(question)<1:
                    errorMessage = "question empty"
                    errorCode = 1010
                    is_pass_check = False

            if answer is None:
                errorMessage = "answer empty"
                errorCode = 1010
                is_pass_check = False
            else:
                if len(answer)<1:
                    errorMessage = "answer empty"
                    errorCode = 1010
                    is_pass_check = False


        if is_pass_check:
            # [TODO]: avoid brute-force attack.
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip
            #log_ret = pincode_log_dbo.add(pincode,serialnumber,request_id,client_md5,remote_ip)
            #print "log_ret", log_ret
            #if not log_ret:
                #errorMessage = "claim_auth log fail"
                #errorCode = 1020
                #is_pass_check = False
                # insert log fail.

            # check pincode & serialnumber
            #logging.info('token:%s, account:%s, serialnumber:%s, remote_ip:%s' % (token, account, serialnumber, remote_ip))
            ret = auth_dbo.security_update(self.current_user['account'], question, answer)

            
        if is_pass_check:
            # every thing is correct
            self.set_status(200)
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #self.render('auth_fail.json', account='u12345')

        return data
