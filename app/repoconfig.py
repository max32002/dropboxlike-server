#!/usr/bin/env python
#encoding=utf-8
import os
import logging
import sqlite3
from dbo.repo import DboRepo
from dbo.pincode import DboPincode
from dbo.pool import DboPool
from dbo.pool import DboPoolSubscriber
from dbo.account import DboAccount
from dbo.account import DboToken

from tornado.options import options

from tornado.util import basestring_type, exec_in
from tornado.escape import _unicode, native_str    


import settings
from app.lib import libHttp
from app.lib import libWSClient
from app.lib import misc
import json

# for terminate app.
import sys

# for short-pincode & changeable & GUI support sultion.
DEFAULT_REG_WAIT_MINUTES = 2

def repo_register(repo_dbo, pincode_dbo):
    ret = False
    # method 1: http get solution.
    http_code,json_obj = call_repo_register_api()
    # method 2: websocket solution.
    #http_code,json_obj = call_repo_register_api_ws()
    if http_code > 0:
        if http_code==200 and not json_obj is None:
            #print "json:", json_obj
            pincode = json_obj.get('pincode','')
            sn = json_obj.get('sn','')
            serialnumber = misc.rand_number(6)
            #sn = misc.rand_number(16)
            #if len(sn) > 0:
                # for short-pincode & changeable & GUI support sultion.
                #display_pincode_to_user(pincode, DEFAULT_REG_WAIT_MINUTES)

            display_pincode_to_user(pincode, serialnumber=serialnumber)
            # clear whole table.
            #repo_dbo.empty()
            pincode_dbo.empty()
            ret = pincode_dbo.add(pincode,serialnumber,sn)

            # auto pooling, after get pincode.
            # for short-pincode & changeable & GUI support sultion.
            #repo_query(repo_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
        else:
            print "unknow error, return json empty!"
            pass
    else:
        #print "server is not able be connected or cancel by user"
        pass

    return ret

# solution 2, websocket
def call_repo_register_api_ws():
    ws = libWSClient.WSClient()
    api_reg_pattern = "1/ws_reg"
    body_dict = prepare_reg_json_body()
    sent_data = json.dumps(dict(action="reg",data=body_dict))
    return ws.connect(options.api_hostname, api_reg_pattern, data=sent_data)


# solution 1, http get
def call_repo_register_api():
    api_reg_pattern = "1/repo/reg"
    api_url = "https://%s/%s" % (options.api_hostname,api_reg_pattern)

    json_body = json.dumps(prepare_reg_json_body())
    #print json_body

    http_obj = libHttp.Http()
    (new_html_string, http_code) = http_obj.get_http_response_core(api_url, data=json_body)
    json_obj = None
    if http_code==200:
        # direct read the string to json.
        json_obj = json.loads(new_html_string)
    else:
        #print "server return error code: %d" % (http_code,)
        #print "server return error message: %s" % (new_html_string,)
        if http_code==400:
            json_obj = None
            try :
                json_obj = json.loads(new_html_string)
            except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                json_obj = None
            except Exception as err:
                json_obj = None
    return http_code,json_obj


def repo_update(repo_token):
    # http get solution.
    http_code,json_obj = call_claimed_repo_update_api(repo_token)
    # websocket solution.
    #http_code,json_obj = call_repo_query_api_ws(pincode, sn, pooling_flag=pooling_flag)
    error_msg = ""
    error_code = 0
    ret = False
    if http_code > 0:
        if not json_obj is None:
            if 'error' in json_obj:
                error_json = json_obj['error']
                if error_json:
                    error_msg = error_json.get('message','')
                    #print "error_msg:%s" % error_msg
                    error_code = error_json.get('code',0)
                    #print "error_msg:%d" % error_code

            if http_code == 200:
                # for shorten pincode version.
                #print "save claimed info to local database..."

                # do nothing for now version.
                ret = True
                pass
            else:
                # for shorten pincode version.
                """
                if error_code in range(1000,1100):
                    # [Too lazy]: assume pincode expire...
                    #print "Pincode expire, get new pincode..."
                    repo_register(repo_dbo, pincode_dbo)
                if error_code == 2000 and not pooling_flag:
                    # only need pooling one time per client.
                    # pincode not expire, need pooling at next time.
                    #print "Start to Pooling... on server side."
                    if len(sn) > 0:
                        display_pincode_to_user(pincode)

                    repo_query(repo_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
                    pass
                """
                pass
        else:
            print "unknow error, return json empty!"
            pass
    else:
        #print "server is not able be connected or cancel by user"
        pass
    return ret, error_code

#def repo_query(repo_dbo, pincode_dbo, pincode, sn, pooling_flag=False):
def repo_query(pincode, sn, pooling_flag=False):
    # http get solution.
    http_code,json_obj = call_repo_query_api(pincode, sn)
    # websocket solution.
    #http_code,json_obj = call_repo_query_api_ws(pincode, sn, pooling_flag=pooling_flag)
    error_msg = ""
    error_code = 0
    ret = False
    if http_code > 0:
        if not json_obj is None:
            if 'error' in json_obj:
                error_json = json_obj['error']
                if error_json:
                    error_msg = error_json.get('message','')
                    #print "error_msg:%s" % error_msg
                    error_code = error_json.get('code',0)
                    #print "error_msg:%d" % error_code

            if http_code == 200:
                # for shorten pincode version.
                #print "save claimed info to local database..."

                # do nothing for now version.
                ret = True
                pass
            else:
                # for shorten pincode version.
                """
                if error_code in range(1000,1100):
                    # [Too lazy]: assume pincode expire...
                    #print "Pincode expire, get new pincode..."
                    repo_register(repo_dbo, pincode_dbo)
                if error_code == 2000 and not pooling_flag:
                    # only need pooling one time per client.
                    # pincode not expire, need pooling at next time.
                    #print "Start to Pooling... on server side."
                    if len(sn) > 0:
                        display_pincode_to_user(pincode)

                    repo_query(repo_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
                    pass
                """
                pass
        else:
            print "unknow error, return json empty!"
            pass
    else:
        #print "server is not able be connected or cancel by user"
        pass

    return ret

# solution 2, websocket
def call_repo_query_api_ws(pincode, sn, pooling_flag=False):
    ws = libWSClient.WSClient()
    api_reg_pattern = "1/ws_reg"
    json_body = {'pincode':pincode, 'sn':sn, 'client_version':options.versionCode}
    sent_data = json.dumps(dict(action="reg_query",data=json_body,pooling_confirmed=pooling_flag))
    return ws.connect(options.api_hostname, api_reg_pattern, data=sent_data)


# solution 1, http
def call_repo_query_api(pincode, sn):
    api_reg_pattern = "1/repo/reg_query"
    api_url = "https://%s/%s" % (options.api_hostname,api_reg_pattern)
    body_dict = prepare_reg_json_body()
    body_dict['pincode']=pincode
    body_dict['sn']=sn
    json_body = json.dumps(body_dict)
    #print json_body

    http_obj = libHttp.Http()
    (new_html_string, http_code) = http_obj.get_http_response_core(api_url, data=json_body)
    json_obj = None
    if http_code==200:
        # direct read the string to json.
        json_obj = json.loads(new_html_string)
    else:
        #print "server return error code: %d" % (http_code,)
        #print "server return error message: %s" % (new_html_string,)
        if http_code==400:
            json_obj = None
            try :
                json_obj = json.loads(new_html_string)
            except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                json_obj = None
            except Exception as err:
                json_obj = None
    return http_code,json_obj


def call_claimed_repo_update_api(repo_token):
    api_reg_pattern = "1/repo/update"
    api_url = "https://%s/%s" % (options.api_hostname,api_reg_pattern)
    body_dict = prepare_reg_json_body()
    body_dict['repo_token']=repo_token
    json_body = json.dumps(body_dict)
    #print json_body

    http_obj = libHttp.Http()
    (new_html_string, http_code) = http_obj.get_http_response_core(api_url, data=json_body)
    json_obj = None
    if http_code==200:
        # direct read the string to json.
        json_obj = json.loads(new_html_string)
    else:
        #print "server return error code: %d" % (http_code,)
        #print "server return error message: %s" % (new_html_string,)
        if http_code==400:
            json_obj = None
            try :
                json_obj = json.loads(new_html_string)
            except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                json_obj = None
            except Exception as err:
                json_obj = None
    return http_code,json_obj

def display_pincode_to_user(pincode, minutes=None, serialnumber=None):
    if len(pincode) > 0:
        message = ""
        message += "Enter PinCode:'%s'" % (pincode)
        if not serialnumber is None:
            message += ", Serial Number:'%s'" % (serialnumber)
        message += " to your mobile phone"
        if not minutes is None:
            message += " in %d minutes.\n" % (minutes)
        else:
            message += ".\n"
        print message


def prepare_reg_json_body():
    import socket
    computerName = socket.gethostname()
    localIp = get_ip_address()

    from uuid import getnode as get_mac
    mac = get_mac()
    mac_formated = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

    data = {'title':computerName,'localIp':localIp, 'port':options.port, 'mac': mac_formated, 'client_version':options.versionCode}
    return data

def get_ip_address():
    import socket
    ip = None
    (hostname, aliaslist, ipaddrlist) = socket.gethostbyname_ex(socket.gethostname())

    localIp = socket.gethostbyname(socket.gethostname())
    if localIp[:4] == "127.":
        ipaddrlist.remove(localIp)

    if len(ipaddrlist) > 0:
        ip = ipaddrlist[len(ipaddrlist)-1]

    if len(ipaddrlist) > 1:
        import netifaces as ni
        interface_arr = ni.interfaces()
        if 'vboxnet0' in interface_arr:
            # {18: [{'addr': '0a:00:27:00:00:00'}], 2: [{'broadcast': '192.168.56.255', 'addr': '192.168.56.1'}]}
            ip = ni.ifaddresses('vboxnet0')[2][0]['addr']
            ipaddrlist.remove(ip)
    #print "ipaddrlist", ipaddrlist
    if len(ipaddrlist) > 0:
        ip = ipaddrlist[len(ipaddrlist)-1]
    return ip

def generate_pincode():
    ret = False
    repo_dbo = None
    pincode_dbo = None
    is_need_terminate_app = False
    is_need_terminate_message = ""

    try:
        client = sqlite3.connect(options.sys_db)
        repo_dbo = DboRepo(client)
        pincode_dbo = DboPincode(client)
        #print "pincode_dbo.rowcount(): %d" % pincode_dbo.rowcount()
        if repo_dbo.rowcount() == 1 and pincode_dbo.rowcount()==0:
            # clean db and try again.
            repo_dbo.empty()

        if repo_dbo.rowcount() == 0:
            # repo empty.
            try:
                is_get_pincode = False
                if pincode_dbo.rowcount() > 0:
                    # pincode/sn exist.
                    # call repo register process - step 2.
                    #pincode_register()
                    pincode_dict = pincode_dbo.first()
                    if not pincode_dict is None:
                        #print "pincode_dict", pincode_dict
                        #print "pincode exist: %s,%s" % (pincode_dict.get('pincode', ''),pincode_dict.get('sn', ''))
                        # start to query pincode.
                        #repo_query(repo_dbo, pincode_dbo, pincode_dict.get('pincode', ''),pincode_dict.get('sn', ''))

                        # server side check.
                        pincode = pincode_dict.get('pincode', '')
                        serialnumber = pincode_dict.get('serialnumber', '')
                        sn = pincode_dict.get('sn', '')
                        if len(pincode) > 0 and len(serialnumber) > 0 and len(sn) > 0:
                            if repo_query(pincode,sn):
                                display_pincode_to_user(pincode, serialnumber=serialnumber)
                                is_get_pincode = True
                            else:
                                # pincode may not exist, try to get NEW pincode again.
                                pass
                        else:
                            # pincode lost, not save currectly.
                            pass
                    else:
                        # unknown error..., try to get NEW pincode again.
                        pass

                if not is_get_pincode:
                    # get pincode again.
                    is_get_pincode = repo_register(repo_dbo, pincode_dbo)
                    if not is_get_pincode:
                        is_need_terminate_app = True
                        is_need_terminate_message = "Can't connect to dropboxlike register server, please try again later"

            except sqlite3.OperationalError as error:
                logging.error("{}.  Please try use add sudo to retry.".format(error))
                is_need_terminate_app = True
                #if "{}".format(error)=="[Errno 13] Permission denied":
            except Exception as error:
                logging.error("{}".format(error))
                raise

        else:
            # repo registered.
            # check repo_token valid.
            ret = True
            repo_dict = repo_dbo.first()
            if not repo_dict is None:
                # server side check.
                repo_update_ret, error_code = repo_update(repo_dict.get('repo_token',''))
                if error_code == 1020:
                    # token expiry or deleted.
                    #print "token expiry or deleted."
                    # [TODO] owner is need to know this error!
                    #repo_dbo.empty()
                    #pincode_dbo.empty()
                    reset_database(client)

                    is_get_pincode = repo_register(repo_dbo, pincode_dbo)
                    if not is_get_pincode:
                        is_need_terminate_message = "Can't connect to dropboxlike register server, please try again later"
                        is_need_terminate_app = True
                    ret = False
                else:
                    # we allow server works during offline(LAN).
                    pass
            else:
                # unknown error...
                is_need_terminate_message = "Can't connect to dropboxlike register server, please try again later"
                is_need_terminate_app = True
                ret = False
                pass
            
            pass
    except sqlite3.OperationalError as error:
        logging.error("{}.  Please try use add sudo to retry.".format(error))
        is_need_terminate_app = True
        #if "{}".format(error)=="[Errno 13] Permission denied":
    except Exception as error:
        logging.error("{}".format(error))
        raise

    if is_need_terminate_app:
        print is_need_terminate_message
        sys.exit()

    return ret

def reset_database(client):
    if not client is None:
        print "Site is unclaimed, database need be reset!"
        repo_dbo = DboRepo(client)
        pincode_dbo = DboPincode(client)
        pool_dbo = DboPool(client)
        pool_subscriber_dbo = DboPoolSubscriber(client)
        account_dbo = DboAccount(client)
        token_dbo = DboToken(client)

        repo_dbo.empty()
        pincode_dbo.empty()
        pool_dbo.empty()
        pool_subscriber_dbo.empty()
        account_dbo.empty()
        token_dbo.empty()


def read_properties(filename, delimiter=':'):
    ''' Reads a given properties file with each line of the format key=value.
        Returns a dictionary containing the pairs.
            filename -- the name of the file to be read
    '''
    open_kwargs = {'mode': 'r', 'newline': ''} if PY3 else {'mode': 'rb'}
    with open(filename, **open_kwargs) as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter, escapechar='\\',
                            quoting=csv.QUOTE_NONE)
        return {row[0]: row[1] for row in reader}

def write_properties(filename, dictionary, delimiter=':'):
    ''' Writes the provided dictionary in key sorted order to a properties
        file with each line in the format: key<delimiter>value
            filename -- the name of the file to be written
            dictionary -- a dictionary containing the key/value pairs.
    '''
    open_kwargs = {'mode': 'w', 'newline': ''} if PY3 else {'mode': 'wb'}
    with open(filename, **open_kwargs) as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter, escapechar='\\',
                            quoting=csv.QUOTE_NONE)
        writer.writerows(sorted(dictionary.items()))


def read_config_file(path):
    ret = True

    config_path = os.path.abspath(path)
    config = {'__file__': config_path}
    new_body = ""
    #print "read config at path:", config_path
    with open(path, 'rb') as f:
        try:
            exec_in(native_str(f.read()), config, config)
        except Exception as error:
            ret = False
            logging.error("Read config file Error: " + path)
            #raise Exception("Parse config file Error: {}".format(error))

    return ret, config


def write_config_file(path, config):
    ret = True
    new_body = ""
    if not config is None:
        for name in config:
            if name[:1] != "_":
                data = config[name]
                #print "name:%s" % name,"config:",config[name]
                if str(data) == "":
                    data = "\"\""

                # our first time flag, don't save
                if name != "doinitial":
                    new_body = new_body + name + "=" + str(data) + "\r\n"
                else:
                    first_time_flag = True

    if len(new_body) > 0:
        try:
            with open(path, "w") as text_file:
                text_file.write(new_body)
        except IOError:
            ret = False
            logging.error("Write config file Error: " + path)
    else:
        ret = False
        logging.error('Config file is empty!')

    return ret


# write user's setting to config file.
def load_config_file():
    CONFIG_FILENAME = "server.conf"

    ret = False
    ret,config = read_config_file(CONFIG_FILENAME)

    if ret:
        if "doinitial" in config:
            # interact with user, to set the environment variables.
            #print "Do first time process..."
            pass

        ret = write_config_file(CONFIG_FILENAME, config)
        if not ret:
            from sys import platform as _platform

            if _platform == "linux" or _platform == "linux2":
               # linux
               logging.error("Because of permission issue, you need run script by: 'sudo ./start' or 'sudo python start.py'")
            elif _platform == "darwin":
               # MAC OS X
               logging.error("Because of permission issue, you need run script by: 'sudo ./start' or 'sudo python start.py'")
            elif _platform == "win32":
               # Windows
               logging.error("you need run script as administrator")
            sys.exit()


    return ret


# PS: set auto_gen_pincode=False to load settings only.
def config_repo(auto_gen_pincode=True):
    ret = False
    if load_config_file():
        # reload settings.
        settings.define_app_options()
        if auto_gen_pincode:
            ret = generate_pincode()
    return ret

if __name__ == "__main__":
    config_repo()