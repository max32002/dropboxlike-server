#!/usr/bin/env python
#encoding=utf-8
import os
#import logging
import sqlite3
from dbo.drive import DboDrive
from tornado.options import options

from tornado.util import basestring_type, exec_in
from tornado.escape import _unicode, native_str    


import settings
from lib import libHttp

def drive_register():
    api_reg_pattern = "1/drive/reg"
    api_hostname = "claim.dropboxlike.com"
    api_url = "https://%s/%s" % (api_hostname,api_reg_pattern)
    http_obj = libHttp.Http()
    (new_html_string, new_http_code) = http_obj.get_http_response_core(api_url)
    #print "return code:%d at packageId:%s" %(new_http_code, packageId)
    json_obj = None
    if new_http_code==200:
        # direct read the string to json.
        json_obj = json.loads(new_html_string)
        if not json_obj is None:
            #print str(json_obj)
            ret = True
            print "json loaded. ^_^"
            pass
    else:
        print "server return error code: %d" % (new_http_code,)
        # error


def setup_db():
    auth_db = options.auth_db
    #logging.info("connecting to database %s ...", auth_db)
    client = sqlite3.connect(auth_db)
    drive_dbo = None
    try:
        drive_dbo = DboDrive(client)
        if drive_dbo.rowcount() == 0:
            # call drive register process.
            drive_register()

    except sqlite3.OperationalError as error:
        print("{}.  Please try use sudo python config.py to retry.".format(error))
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


def parse_config_file(path):
    ret = True

    config = {'__file__': os.path.abspath(path)}
    new_body = ""
    with open(path, 'rb') as f:
        try:
            exec_in(native_str(f.read()), config, config)
        except Exception as error:
            #print("Error: {}".format(error))
            ret = False
            print("Parse config file Error: "+path)
            #raise Exception("Parse config file Error: {}".format(error))

    if  ret:
        for name in config:
            if name[:1] != "_":
                data = config[name]
                #print "name:%s" % name,"config:",config[name]
                if str(data) == "":
                    data = "\"\""
                new_body = new_body + name + "=" + str(data) + "\r\n"
        
        with open(path, "w") as text_file:
            text_file.write(new_body)

    return ret

# write user's setting to config file.
def set_config_file():
    CONFIG_FILENAME = "server.conf"
    return parse_config_file(CONFIG_FILENAME)


if __name__ == "__main__":
    ret = set_config_file()
    if ret:
        settings.define_app_options()
        setup_db()