#!/usr/bin/env python
#encoding=utf-8
import os
#import logging
import sqlite3
from dbo.drive import DboDrive
from dbo.pincode import DboPincode
from tornado.options import options

from tornado.util import basestring_type, exec_in
from tornado.escape import _unicode, native_str    


import settings
from lib import libHttp
from lib import libWSClient
from lib import misc
import json

# for terminate app.
import sys

# for short-pincode & changeable & GUI support sultion.
DEFAULT_REG_WAIT_MINUTES = 2

def drive_register(drive_dbo, pincode_dbo):
    ret = False
    # method 1: http get solution.
    http_code,json_obj = call_drive_register_api()
    # method 2: websocket solution.
    #http_code,json_obj = call_drive_register_api_ws()
    if http_code > 0:
        if not json_obj is None:
            #print "json:", json_obj
            pincode = json_obj.get('pincode','')
            sn = json_obj.get('sn','')
            password = misc.rand_number(6)
            #sn = misc.rand_number(16)
            #if len(sn) > 0:
                # for short-pincode & changeable & GUI support sultion.
                #display_pincode_to_user(pincode, DEFAULT_REG_WAIT_MINUTES)

            display_pincode_to_user(pincode, password=password)
            # clear whole table.
            #drive_dbo.empty()
            pincode_dbo.empty()
            ret, save_dic = pincode_dbo.add(pincode,password,sn)

            # auto pooling, after get pincode.
            # for short-pincode & changeable & GUI support sultion.
            #drive_query(drive_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
        else:
            print "unknow error, return json empty!"
            pass
    else:
        #print "server is not able be connected or cancel by user"
        pass

    return ret

# solution 2, websocket
def call_drive_register_api_ws():
    ws = libWSClient.WSClient()
    #api_hostname = "claim.dropboxlike.com"
    api_hostname = "127.0.0.1"
    api_reg_pattern = "1/ws_reg"
    json_body = prepare_reg_json_body()
    sent_data = json.dumps(dict(action="reg",data=json_body))
    return ws.connect(api_hostname, api_reg_pattern, data=sent_data)


# solution 1, http get
def call_drive_register_api():
    api_reg_pattern = "1/drive/reg"
    #api_hostname = "claim.dropboxlike.com"
    api_hostname = "127.0.0.1"
    api_url = "https://%s/%s" % (api_hostname,api_reg_pattern)

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
        pass
        # error
    return http_code,json_obj


def drive_query(drive_dbo, pincode_dbo, pincode, sn, pooling_flag=False):
    # http get solution.
    http_code,json_obj = call_drive_query_api(pincode, sn)
    # websocket solution.
    #http_code,json_obj = call_drive_query_api_ws(pincode, sn, pooling_flag=pooling_flag)
    if http_code > 0:
        if not json_obj is None:
            if 'error' in json_obj:
                error_json = json_obj['error']
                error_msg = error_json.get('message','')
                #print "error_msg:%s" % error_msg
                error_code = error_json.get('code',0)
                #print "error_msg:%d" % error_code

            if http_code == 200:
                # 
                pass
                #print "save claimed info to local database..."
            else:
                if error_code in range(1000,1100):
                    # [Too lazy]: assume pincode expire...
                    #print "Pincode expire, get new pincode..."
                    drive_register(drive_dbo, pincode_dbo)
                if error_code == 2000 and not pooling_flag:
                    # only need pooling one time per client.
                    # pincode not expire, need pooling at next time.
                    #print "Start to Pooling... on server side."
                    if len(sn) > 0:
                        display_pincode_to_user(pincode)

                    drive_query(drive_dbo, pincode_dbo, pincode, sn, pooling_flag=True)
                    pass
        else:
            print "unknow error, return json empty!"
            pass
    else:
        #print "server is not able be connected or cancel by user"
        pass


# solution 2, websocket
def call_drive_query_api_ws(pincode, sn, pooling_flag=False):
    ws = libWSClient.WSClient()
    #api_hostname = "claim.dropboxlike.com"
    api_hostname = "127.0.0.1"
    api_reg_pattern = "1/ws_reg"
    json_body = {'pincode':pincode, 'sn':sn, 'client_version':options.versionCode}
    sent_data = json.dumps(dict(action="reg_query",data=json_body,pooling_confirmed=pooling_flag))
    return ws.connect(api_hostname, api_reg_pattern, data=sent_data)


# solution 1, http
# Deprecated
def call_drive_query_api(pincode, sn):
    api_reg_pattern = "1/drive/reg_query"
    #api_hostname = "claim.dropboxlike.com"
    api_hostname = "127.0.0.1"
    api_url = "https://%s/%s" % (api_hostname,api_reg_pattern)

    json_body = json.dumps({'pincode':pincode, 'sn':sn, 'client_version':options.versionCode})
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
                #print('except:%s' % (str(err)))
                json_obj = None
            except Exception as err:
                #print('except:%s' % (str(err)))
                json_obj = None
    return http_code,json_obj


def display_pincode_to_user(pincode, minutes=None, password=None):
    if len(pincode) > 0:
        message = ""
        message += "Enter PinCode:'%s'" % (pincode)
        if not password is None:
            message += ", Password: '%s'" % (password)
        message += " to your mobile phone"
        if not minutes is None:
            message += " in %d minutes.\n" % (minutes)
        else:
            message += ".\n"
        print message


def prepare_reg_json_body():
    import socket
    computerName = socket.gethostname()
    localIp = socket.gethostbyname(socket.gethostname())

    from uuid import getnode as get_mac
    mac = get_mac()
    mac_formated = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

    data = {'title':computerName,'localIp':localIp, 'port':options.port, 'mac': mac_formated, 'client_version':options.versionCode}
    return data


def generate_pincode():
    ret = False
    client = sqlite3.connect(options.sys_db)
    drive_dbo = None
    pincode_dbo = None

    try:
        drive_dbo = DboDrive(client)
        pincode_dbo = DboPincode(client)
        #print "pincode_dbo.rowcount(): %d" % pincode_dbo.rowcount()
        if drive_dbo.rowcount() == 1 and pincode_dbo.rowcount()==0:
            # clean db and try again.
            drive_dbo.empty()

        if drive_dbo.rowcount() == 0:
            # drive empty.
            try:
                error_msg = ""
                is_get_pincode = False
                if pincode_dbo.rowcount() == 0:
                    # call drive register process - step 1.
                    is_get_pincode = drive_register(drive_dbo, pincode_dbo)
                    if not is_get_pincode:
                        error_msg = "Can't connect to dropboxlike register server, please try again later"
                else:
                    # pincode/sn exist.
                    # call drive register process - step 2.
                    #pincode_register()
                    pincode_dict = pincode_dbo.first()
                    if not pincode_dict is None:
                        #print "pincode_dict", pincode_dict
                        #print "pincode exist: %s,%s" % (pincode_dict.get('pincode', ''),pincode_dict.get('sn', ''))
                        # start to query pincode.
                        #drive_query(drive_dbo, pincode_dbo, pincode_dict.get('pincode', ''),pincode_dict.get('sn', ''))
                        display_pincode_to_user(pincode_dict.get('pincode', ''), password=pincode_dict.get('password', ''))
                        is_get_pincode = True
                    else:
                        # unknown error...
                        error_msg = "Can't get pincode from database, please delete dropboxlike.db than launch application agage."
                        pass

                if not is_get_pincode:
                    print error_msg
                    sys.exit()
                    
            except sqlite3.OperationalError as error:
                print("{}.  Please try use add sudo to retry.".format(error))
                #if "{}".format(error)=="[Errno 13] Permission denied":
            except Exception as error:
                print("{}".format(error))
                raise

        else:
            # drive registered.
            ret = True
            pass
    except sqlite3.OperationalError as error:
        print("{}.  Please try use add sudo to retry.".format(error))
        #if "{}".format(error)=="[Errno 13] Permission denied":
    except Exception as error:
        print("{}".format(error))
        raise

    return ret


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

    config = {'__file__': os.path.abspath(path)}
    new_body = ""
    with open(path, 'rb') as f:
        try:
            exec_in(native_str(f.read()), config, config)
        except Exception as error:
            #print("Error: {}".format(error))
            ret = False
            print("Read config file Error: " + path)
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
            print("Write config file Error: " + path)
    else:
        ret = False
        print 'Config file is empty!'

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

    return ret


def driverconfig():
    ret = False
    if load_config_file():
        # reload settings.
        settings.define_app_options()
        ret = generate_pincode()
    return ret

if __name__ == "__main__":
    driverconfig()