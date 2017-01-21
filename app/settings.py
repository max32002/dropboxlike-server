#!/usr/bin/env python
#fileencoding=utf-8

import logging
from tornado.options import define
from tornado.options import options
import tempfile
import os


def define_app_options():
    #define('debug', False)
    define('debug', True)

    define('log_level', default=logging.INFO)
    define('log_backup_path', default=tempfile.gettempdir())
    
    define('versionCode', 1)
    define('versionName', "1.0")

    default_port = 443
    define('port', default_port)

    database_schema_version = 1
    define('database_schema_version', database_schema_version)

    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

    storage_access_point = os.path.join(app_root, 'storage')
    define('storage_access_point', default=storage_access_point)

    certificate_path = os.path.join(app_root, 'app/certs')
    define('certificate_path', default=certificate_path)

    sys_db = os.path.join(options.storage_access_point, 'dropboxlike.db')
    define('sys_db', default=sys_db)

    define('ignore_token_check_prefix', default=['/1/auth/','/version'])
    define('claim_uri_prefix', default=['/1/repo/claim_auth'])
    #define('api_hostname', 'claimapi.dropboxlike.com')
    define('api_hostname', '127.0.0.1')

    conf_filepath = os.path.join(app_root, 'server.conf')
    #print "config filepath: %s" % conf_filepath
    #print "auth_db filepath: %s" % auth_db
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


    


