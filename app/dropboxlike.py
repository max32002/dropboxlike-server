#!/usr/bin/env python
#encoding=utf-8

import os
import logging

from tornado.httpserver import HTTPServer
from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.options import options, parse_command_line
from jinja2 import ChoiceLoader, FileSystemLoader

from app.lib.template import JinjaLoader
from app.lib.misc import install_tornado_shutdown_handler

import sqlite3
from app.dbo.schema_version import DboSchemaVersion

#import settings
import app.repoconfig

class MaxDropboxLikeWeb(object):
    def get_settings(self, proj_template_path, proj_static_paths):
        #settings.define_app_options()
        claimed = app.repoconfig.config_repo()

        parse_command_line(final=True)

        self_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
        loader = ChoiceLoader([
            FileSystemLoader(proj_template_path),
            FileSystemLoader(os.path.join(self_dir_path, '../templates')),
            ])

        return {
            'template_loader': JinjaLoader(loader=loader, auto_escape=False),
            'debug': options.debug,
            'claimed': claimed
        }

    def __init__(self, routes, template_path, proj_static_paths=[],
                 **more_settings):
        the_settings = self.get_settings(template_path, proj_static_paths)
        the_settings.update(more_settings)

        self.app = Application(routes, **the_settings)
        self.app.sql_client = self.setup_db()
        self.app.claimed = the_settings['claimed']

    def setup_db(self):
        #logging.info("connecting to database %s ...", options.sys_db)
        client = sqlite3.connect(options.sys_db)
        schema_dbo = DboSchemaVersion(client)
        schema_dbo.auto_upgrade()
        return client

    def run(self):
        #logging.info('Runing at port %s in %s mode', options.port, 'debug' if options.debug else 'production')

        claimed_status = "unclaimed"
        if self.app.claimed:
            claimed_status = "claimed"
        logging.info('Runing %s dropboxlike at port %s, press Ctrl+C to stop.', claimed_status, options.port)
        server = HTTPServer(self.app, xheaders=True, ssl_options = {
    "certfile": os.path.join(options.certificate_path, "server.crt"),
    "keyfile": os.path.join(options.certificate_path, "server.key"),
})
        is_listening = False
        try:
            server.listen(options.port)
            is_listening = True
        except Exception as error:
            #print("Error: {}".format(error))
            if "{}".format(error)=="[Errno 13] Permission denied":
                from sys import platform as _platform

                if _platform == "linux" or _platform == "linux2":
                   # linux
                   logging.error("Because of permission issue, you need run script by: sudo python start.py")
                elif _platform == "darwin":
                   # MAC OS X
                   logging.error("Because of permission issue, you need run script by: sudo python start.py")
                elif _platform == "win32":
                   # Windows
                   logging.error("you need run script as administrator")
            else:
                #raise
                print("Error: {}".format(error))
                pass
        
        if is_listening:
            install_tornado_shutdown_handler(IOLoop.instance(), server)
            logging.info('Good to go!')

            IOLoop.instance().start()
            #logging.info('Exiting...waiting for background jobs done...')
            #logging.info('Done. Bye.')
            logging.info('Bye.')

