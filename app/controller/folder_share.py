#!/usr/bin/env python
#encoding=utf-8
from app.handlers import BaseHandler
import logging
import json
from tornado.options import options
from app.lib import libHttp
from app.lib import misc
from app.dbo.repo import DboRepo
from app.dbo import dbconst
from app.dbo.pool import DboPool
from app.dbo.pool import DboPoolSubscriber
from app.dbo.folder_sharing import DboFolderSharing
from app.controller.meta_manager import MetaManager
import os

class FolderShareCreateHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        folder_sharing_dbo = DboFolderSharing(self.application.sql_client)
        auth_dbo = self.db_account

        errorMessage = ""
        errorCode = 0
        is_pass_check = True

        if folder_sharing_dbo is None:
            errorMessage = "database return null"
            errorCode = 1001
            is_pass_check = False

        #logging.info("body:"+self.request.body)
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

        password = None
        path = None
        can_edit = 0
        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    if 'password' in _body:
                        password = _body['password']
                    if 'path' in _body:
                        path = _body['path']
                    if 'can_edit' in _body:
                        if _body['can_edit']:
                            can_edit=1
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1004
                    pass

        if is_pass_check:
            if password is None:
                password = ""
            else:
                if len(str(password))<4 and len(str(password))>0:
                    errorMessage = "password too short"
                    errorCode = 1005

        if is_pass_check:
            ret, errorMessage = self.check_path(path)
            if not ret:
                is_pass_check = False
                errorCode = 1010

        if is_pass_check:
            if path=="/":
                path = ""

            if len(path)==0:
                errorMessage = "path is empty"
                errorCode = 1013
                is_pass_check = False

        if is_pass_check:
            if self.current_user['poolid'] is None:
                errorMessage = "no share permission"
                errorCode = 1015
                is_pass_check = False
                    
        old_real_path = None
        old_poolid = None
        if is_pass_check:
            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)

            old_real_path = self.metadata_manager.real_path
            old_poolid = self.metadata_manager.poolid
            if not old_real_path is None:
                if not os.path.exists(old_real_path):
                    # path not exist
                    errorMessage = "real path is not exist"
                    errorCode = 1020
                    is_pass_check = False
            else:
                errorMessage = "no permission"
                errorCode = 1030
                is_pass_check = False

        shared_folder_pool_array = []
        if is_pass_check:
            dbo_pool_sub = DboPoolSubscriber(self.application.sql_client)
            user_account = self.current_user['account']
            shared_folder_pool_array = dbo_pool_sub.contain_share_poolid(user_account, path)
            #print "shared_folder_pool_array",  shared_folder_pool_array
            if len(shared_folder_pool_array) > 0:
                errorMessage = "unable to create share folder which contain share folder"
                errorCode = 1031
                is_pass_check = False

        if is_pass_check:
            if self.current_user['poolid'] != old_poolid:
                errorMessage = "unable to share folder under share folder"
                errorCode = 1032
                is_pass_check = False

        ret_dict = {}
        ret_dict['password']=password
        if is_pass_check:
            # start check on public server.
            is_pass_check = False

            http_code,json_obj = self.call_folder_sharing_reg_api()
            if http_code > 0:
                if http_code == 200 and not json_obj is None:
                    #print "json:", json_obj
                    share_code = json_obj.get('share_code','')
                    share_code = share_code.lower()
                    if len(share_code) > 0:
                        user_account = self.current_user['account']
                        is_pass_check, new_poolid, errorMessage, errorCode = self.create_shared_folder_pool(user_account, path)
                        if not is_pass_check:
                            errorMessage = "create new pool to database fail"
                            errorCode = 1042

                        if is_pass_check:
                            old_poolid = self.current_user['poolid']
                            self.metadata_manager = MetaManager(self.application.sql_client, self.current_user, path)
                            is_pass_check, current_metadata, errorMessage = self.metadata_manager.move_metadata(old_poolid, path)
                            if is_pass_check:
                                is_pass_check = folder_sharing_dbo.add(share_code, password, new_poolid, can_edit)
                                if not is_pass_check:
                                    errorMessage = "insert new folder sharing info to database fail"
                                    errorCode = 1043
                            if is_pass_check:
                                # move direct
                                is_pass_check = self.move_shared_folder_to_pool(new_poolid, old_real_path)
                                if not is_pass_check:
                                    errorMessage = "move folder to new path fail"
                                    errorCode = 1044
                    else:
                        errorMessage = "share_code return empty"
                        errorCode = 1041

                    if is_pass_check:
                        if len(password) > 0:
                            share_code = share_code + "1"
                        ret_dict['share_code'] = share_code

                if http_code >= 400 and http_code <= 403 and not json_obj is None:
                    # by pass the error message
                    is_pass_check = False
                    error_json = json_obj.get('error',None)
                    if not error_json is None:
                        errorMessage = error_json.get('message','')
                        errorCode = error_json.get('code',0)
            else:
                errorMessage = "login server is not able to connect."
                errorCode = 1040
            
        if is_pass_check:
            # every thing is correct
            self.set_status(200)
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))

    def move_shared_folder_to_pool(self, poolid, old_real_path):
        ret = False
        if poolid > 0:
            pool_home = '%s/storagepool/%s' % (options.storage_access_point, poolid)
            if not os.path.exists(pool_home):
                import shutil
                shutil.move(old_real_path, pool_home)
                ret = True
            else:
                # error
                pass
        return ret

    def create_shared_folder_pool(self, user_account, localpoolname):
        errorMessage = ""
        errorCode = 0

        is_root = 0
        pool_dbo = DboPool(self.application.sql_client)

        # TOOD: here should begin trans. and able to rollback.
        is_pass_check, poolid = pool_dbo.add(user_account, is_root)
        if is_pass_check:
            if poolid > 0:
                #localpoolname = path
                can_edit = 1
                status = dbconst.POOL_STATUS_SHARED

                pool_subscriber_dbo = DboPoolSubscriber(self.application.sql_client)
                is_pass_check = pool_subscriber_dbo.add(user_account, poolid, localpoolname, can_edit, status)
                if not is_pass_check:
                    errorMessage = "Add new pool_subscriber fail"
                    errorCode = 1032
            else:
                is_pass_check = False
                errorMessage = "poolid is wrong"
                errorCode = 1031
        else:
            errorMessage = "Add new pool fail"
            errorCode = 1030

        return is_pass_check, poolid, errorMessage, errorCode

    def call_folder_sharing_reg_api(self):
        api_reg_pattern = "1/repo/share/reg_folder"
        api_url = "https://%s/%s" % (options.api_hostname,api_reg_pattern)

        confirm_dict = {}
        repo_dbo = DboRepo(self.application.sql_client)
        repo_dict = repo_dbo.first()
        if not repo_dict is None:
            confirm_dict['repo_token'] = repo_dict['repo_token']
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

class FolderShareAuthHandler(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        auth_dbo = self.db_account
        folder_sharing_dbo = DboFolderSharing(self.application.sql_client)

        errorMessage = ""
        errorCode = 0

        #logging.info('body:%s' % (self.request.body))
        is_pass_check = True
        
        if folder_sharing_dbo is None:
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
                errorCode = 1002
                pass

        share_code = None
        request_id = None
        password = ""

        if is_pass_check:
            is_pass_check = False
            if _body:
                try :
                    if 'share_code' in _body:
                        share_code = _body['share_code'][:16]
                    if 'request_id' in _body:
                        request_id = _body['request_id']
                    if 'password' in _body:
                        password = _body['password']
                    is_pass_check = True
                except Exception:
                    errorMessage = "parse json fail"
                    errorCode = 1004
                    pass

        if is_pass_check:
            if share_code is None:
                errorMessage = "share_code empty"
                errorCode = 1010
                is_pass_check = False
            else:
                if len(share_code)<16:
                    errorMessage = "share_code malformat"
                    errorCode = 1010
                    is_pass_check = False

            if request_id is None:
                errorMessage = "request_id empty"
                errorCode = 1012
                is_pass_check = False

        if is_pass_check:
            if password is None:
                password = ""

        if is_pass_check:
            # [TODO]: Password brute-force attack.
            x_real_ip = self.request.headers.get("X-Real-IP")
            remote_ip = self.request.remote_ip if not x_real_ip else x_real_ip

        sharing_dict = None
        if is_pass_check:
            sharing_dict = folder_sharing_dbo.match(share_code, password)
            if sharing_dict is None:
                errorMessage = "Password not match"
                errorCode = 1021
                is_pass_check = False

        ret_dict = {}
        ret_dict['share_code'] = share_code

        user_account = ""
        user_password = ""

        if is_pass_check:
            # start check on public server.
            is_pass_check = False

            http_code,json_obj = self.call_folder_sharing_confirm_api(share_code, request_id)
            if http_code > 0:
                if http_code == 200 and not json_obj is None:
                    #print "json:", json_obj
                    account_sn = json_obj.get('account_sn','')

                    ret_dict['account_sn'] = account_sn

                    ret, user_account, user_password = auth_dbo.is_account_sn_exist(account_sn);

                    if not ret:
                        # new user.
                        is_owner=0
                        ret,user_account,user_password = auth_dbo.new_user(is_owner, account_sn=account_sn)
                        #print "new user:",ret,account,password
                        if ret and len(user_account) > 0 and len(user_password) > 0:
                            #account_info = "%s,%s" % (user_account,user_password)
                            is_pass_check = True
                        else:
                            errorMessage = "create new user fail"
                            errorCode = 1040

                    else:
                        # shared folder user.
                        is_pass_check = True
                        pass

                    ret_dict['account'] = user_account
                    ret_dict['password'] = user_password


                if http_code >= 400 and http_code <= 403 and not json_obj is None:
                    # by pass the error message
                    is_pass_check = False
                    error_json = json_obj.get('error',None)
                    if not error_json is None:
                        errorMessage = error_json.get('message','')
                        errorCode = error_json.get('code',0)

            else:
                #print "server is not able be connected or cancel by user"
                pass

        if is_pass_check:
            is_pass_check, errorMessage, errorCode = self.create_shared_repo_pool(user_account)

        if is_pass_check:
            # clean_folder_sharing
            is_pass_check=folder_sharing_dbo.pk_delete(share_code)
            if not is_pass_check:
                errorMessage = "Remove share_code fail"
                errorCode = 1041

            
        if is_pass_check:
            # every thing is correct
            self.set_status(200)
            self.write(ret_dict)
        else:
            self.set_status(400)
            self.write(dict(error=dict(message=errorMessage,code=errorCode)))
            #logging.error('%s' % (str(dict(error=dict(message=errorMessage,code=errorCode)))))

    def create_shared_repo_pool(self, user_account):
        errorMessage = ""
        errorCode = 0

        is_root = 1
        pool_dbo = DboPool(self.application.sql_client)

        # TOOD: here should begin trans. and able to rollback.
        is_pass_check, poolid = pool_dbo.add(user_account, is_root)
        if is_pass_check:
            if poolid > 0:
                localpoolname = ""
                can_edit = 1
                status = dbconst.POOL_STATUS_OWNER

                pool_subscriber_dbo = DboPoolSubscriber(self.application.sql_client)
                is_pass_check = pool_subscriber_dbo.add(user_account, poolid, localpoolname, can_edit, status)
                if not is_pass_check:
                    errorMessage = "Add new pool_subscriber fail"
                    errorCode = 1032
            else:
                is_pass_check = False
                errorMessage = "poolid is wrong"
                errorCode = 1031
        else:
            errorMessage = "Add new pool fail"
            errorCode = 1030

        if is_pass_check:
            if poolid > 0:
                user_home = '%s/storagepool/%s' % (options.storage_access_point, poolid)
                self._mkdir_recursive(user_home)

                from app.controller.meta_manager import MetaManager
                user_dict = {'account':user_account,'poolid':poolid}
                metadata_manager = MetaManager(self.application.sql_client, user_dict, "")
                is_pass_check, query_result, errorMessage = metadata_manager.add_metadata(is_dir=1)
                #print "query_result", query_result
                if not is_pass_check:
                    errorMessage = "add metadata in database fail"
                    errorCode = 1040

        return is_pass_check, errorMessage, errorCode

    def _mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def call_folder_sharing_confirm_api(self, share_code, request_id):
        api_reg_pattern = "1/repo/share/confirm_folder"
        api_url = "https://%s/%s" % (options.api_hostname,api_reg_pattern)

        confirm_dict = {}
        repo_dbo = DboRepo(self.application.sql_client)
        repo_dict = repo_dbo.first()
        if not repo_dict is None:
            confirm_dict['repo_token'] = repo_dict['repo_token']
        confirm_dict['share_code'] = share_code
        confirm_dict['request_id'] = request_id
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
