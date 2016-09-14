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
import json

def drive_register(drive_dbo, pincode_dbo):
    json_obj = call_drive_register_api()
    if not json_obj is None:
        pinCode,sn = show_pincode_to_user(json_obj)
        if len(sn) > 0:
            pincode_dbo.empty()
            result, save_dic = pincode_dbo.add(pinCode,sn)


def call_drive_register_api():
    api_reg_pattern = "1/drive/reg"
    #api_hostname = "claim.dropboxlike.com"
    api_hostname = "127.0.0.1"
    api_url = "https://%s/%s" % (api_hostname,api_reg_pattern)

    json_body = prepare_reg_json_body()
    #print json_body

    http_obj = libHttp.Http()
    (new_html_string, new_http_code) = http_obj.get_http_response_core(api_url, data=json_body)
    #print "return code:%d at packageId:%s" %(new_http_code, packageId)
    json_obj = None
    if new_http_code==200:
        # direct read the string to json.
        json_obj = json.loads(new_html_string)
    else:
        print "server return error code: %d" % (new_http_code,)
        # error
    return json_obj


def show_pincode_to_user(json_obj):
    pinCode = ""
    #print json_obj
    pinCode = json_obj.get('pinCode','')
    sn = json_obj.get('sn','')
    if len(pinCode) > 0:
        print "Enter PinCode '%s' to your mobile phone in 2 minutes"\
                    % pinCode
    
    return pinCode,sn


def prepare_reg_json_body():
    import socket
    computerName = socket.gethostname()
    localIp = socket.gethostbyname(socket.gethostname())
#!/usr/bin/env python
#encoding=utf-8

    from uuid import getnode as get_mac
    mac = get_mac()
    mac_formated = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))

    data = {'title':computerName,'localIp':localIp, 'port':options.port, 'mac': mac_formated, 'client_version':options.versionCode}
    return json.dumps(data)


def setup_db():
    auth_db = options.auth_db
    #logging.info("connecting to database %s ...", auth_db)
    client = sqlite3.connect(auth_db)
    drive_dbo = None
    pincode_dbo = None

    try:
        drive_dbo = DboDrive(client)
        if drive_dbo.rowcount() == 0:
            # drive empty.
            try:
                pincode_dbo = DboPincode(client)
                #print "pincode_dbo.rowcount(): %d" % pincode_dbo.rowcount()
                if pincode_dbo.rowcount() == 0:
                    # call drive register process - step 1.
                    drive_register(drive_dbo, pincode_dbo)
                else:
                    # pincode/sn exist.
                    # call drive register process - step 2.
                    #pincode_register()
                    pincode_list = pincode_dbo.first()
                    pincode_dict = None
                    if not pincode_list is None:
                        pincode_dict = pincode_list[0]
                        if not pincode_dict is None:
                            print "pincode exist: %s,%s" % (pincode_dict.get('pincode', ''),pincode_dict.get('sn', ''))
                    pass
            except sqlite3.OperationalError as error:
                print("{}.  Please try use add sudo to retry.".format(error))
                #if "{}".format(error)=="[Errno 13] Permission denied":
            except Exception as error:
                print("{}".format(error))
                raise

        else:
            # drive registered.
            pass
    except sqlite3.OperationalError as error:
        print("{}.  Please try use add sudo to retry.".format(error))
        #if "{}".format(error)=="[Errno 13] Permission denied":
    except Exception as error:
        print("{}".format(error))
        raise



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
    if load_config_file():
        # reload settings.
        settings.define_app_options()
        setup_db()

if __name__ == "__main__":
    driverconfig()