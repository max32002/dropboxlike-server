#!/usr/bin/env python
#encoding=utf-8
import os
import errno
import app.repoconfig
from tornado.options import options
from app.dbo.account import DboAccount
import sqlite3

if __name__ == "__main__":
    ret = app.repoconfig.config_repo(auto_gen_pincode=False)
    db_location = options.sys_db
    #print "location:", options.storage_access_point

    message = ""
    try :
        conn = sqlite3.connect(db_location)
        dbo_account = DboAccount(conn)
        dbo_account.reset_all_security_question()
        message = "All security question has been reset."
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
