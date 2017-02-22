#!/usr/bin/env python
#encoding=utf-8
import os
import errno
import app.repoconfig
from tornado.options import options
import shutil


if __name__ == "__main__":
    ret = app.repoconfig.config_repo(auto_gen_pincode=False)
    message = ""
    try :
        if os.path.exists(options.storage_access_point):
            # backup before delete.
            shutil.rmtree(options.storage_access_point)
        message = "all removed: " + options.storage_access_point
    except Exception, err:
        errorMessage = "{}".format(err)
        # not is json format.
        if hasattr(err, 'errno'):
            if err.errno == errno.EACCES:
                errorMessage = "Database file is locked, please use sudo to try again."
        #print errorMessage
        message = errorMessage
        pass

    print message
