#!/usr/bin/env python
#encoding=utf-8
import os
import errno
import app.repoconfig
from tornado.options import options

if __name__ == "__main__":
    ret = app.repoconfig.config_repo(auto_gen_pincode=False)
    db_location = options.sys_db
    #print "location:", options.storage_access_point
    message = ""
    try :
        if os.path.exists(db_location):
            os.remove(db_location)
        message = "file removed: " + db_location
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
