#!/usr/bin/env python
#fileencoding=utf-8

import re
import time
import random
import string
import logging

from bson.json_util import dumps, loads
from bson.objectid import ObjectId

from app.lib import data_file

class UploadHandler(BaseHandler):
    def post(self):
        f = self.request.files['file'][0]
        f_data = f['body']
        f_type = f['filename'].split('.')[-1]
        f_url = self.img_prefix + data_file.save(
            self.img_store_path, f_data, f_type)

        self.write(f_url)
        logging.info("%s uploaded img %s",
                     self.current_user['email'], f_url)
