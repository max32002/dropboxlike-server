#!/usr/bin/env python
#fileencoding=utf-8

import os
import md5
import shutil

_builtin_open = open


def ensure_dir_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)
\
def save(abspath, content):
    ret = False
    message = ""
    dirname = os.path.dirname(abspath)
    ensure_dir_exist(dirname)

    tmp_abspath = '{}.tmp.{}'.format(abspath, os.getpid())
    try:
        # [TODO] handle special case: exist file locked.

        # [TODO] handel special case: disk no free space.

        with _builtin_open(tmp_abspath, "wb") as fobj:
            fobj.write(content)
        shutil.move(tmp_abspath, abspath)

        message = os.path.basename(abspath)

        ret = True
    except Exception as error:
        errorMessage = "{}".format(error)
        logging.error(errorMessage)
        message = errorMessage


    return ret, message
