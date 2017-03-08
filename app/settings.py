#!/usr/bin/env python
#fileencoding=utf-8

import logging
from tornado.options import define
from tornado.options import options
import tempfile
import os
import sys


def define_app_options():
    #define('debug', False)
    define('debug', True)

    define('log_level', default=logging.INFO)
    define('log_backup_path', default=tempfile.gettempdir())
    
    define('versionCode', 3)
    define('versionName', "1.2")

    default_port = 443
    define('port', default_port)

    database_schema_version = 1
    define('database_schema_version', database_schema_version)

    basis = ""
    if hasattr(sys, 'frozen'):
        basis = sys.executable
    else:
        basis = sys.argv[0]
    app_root = os.path.dirname(basis)

    storage_access_point = os.path.join(app_root, 'storage')
    define('storage_access_point', default=storage_access_point)

    certificate_path = os.path.join(app_root, 'certs')
    define('certificate_path', default=certificate_path)

    sys_db = os.path.join(options.storage_access_point, 'dropboxlike.db')
    define('sys_db', default=sys_db)

    define('ignore_token_check_prefix', default=['/1/auth/','/server_info','/1/repo/auth_shared_repo'])
    define('claim_uri_prefix', default=['/1/repo/claim_auth'])
    define('api_hostname', 'api.dropboxlike.com')
    #define('api_hostname', '127.0.0.1')

    conf_filepath = os.path.join(app_root, 'server.conf')
    #print "config filepath: %s" % conf_filepath
    #print "auth_db filepath: %s" % auth_db
    if os.path.isfile(conf_filepath):
        options.parse_config_file(conf_filepath)

    # reload storage_access_point from config.
    if options.port is None:
        define('port', default_port)

    if not options.storage_access_point is None:
        if len(options.storage_access_point) < 1:
            define('storage_access_point', default=storage_access_point)
        else:
            pass
    else:
        define('storage_access_point', default=storage_access_point)

    # should create not exist folder for storage.
    if not os.path.exists(options.storage_access_point):
        os.makedirs(options.storage_access_point)


    


