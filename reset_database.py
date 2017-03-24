#!/usr/bin/env python
#encoding=utf-8
import os
import errno
import app.repoconfig
from tornado.options import options
from shutil import copyfile


# open database.
#[TODO] multi-database solution.
#def open_metadata(self, poolid):
def get_metadata_db_path(poolid):
    db_path = u'%s/metadata.db' % (options.storage_access_point)
    #logging.info("open metadata poolid: %s ... ", db_path)
    return db_path

def back_db_file(db_location):
    message=""
    try:
        db_location_bak = db_location + ".bak"
        if os.path.exists(db_location):
            # backup before delete.
            copyfile(db_location, db_location_bak)
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
    return message

if __name__ == "__main__":
    ret = app.repoconfig.config_repo(auto_gen_pincode=False)
    db_location = options.sys_db
    #print "location:", options.storage_access_point
    message_main = back_db_file(db_location)
    if len(message_main) > 0:
        db_location = get_metadata_db_path(1)
        message_metadata = back_db_file(db_location)
        if len(message_metadata) > 0:
            message_main = message_main + "\n" + message_metadata
    print message_main
