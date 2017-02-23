from tornado.options import options
import logging
from app.dbo.thumbnail import DboThumbnail
import sqlite3
from app.lib import thumbnail

class ThumbnailManager():
    dbo_thumbnail = None

    def __init__(self, thumbnail_conn):
        self.dbo_thumbnail = DboThumbnail(thumbnail_conn)

    def is_image(self, real_path):
        return thumbnail.isSupportedFormat(real_path)

    def add(self, real_path):
        if(self.is_image(real_path)):
            logging.info("start to add thumbnail: %s ... ", real_path)
            out_dic = self.get_new_thumbnail_id()
            if not out_dic is None:
                if 'lastrowid' in out_dic:
                    doc_id = out_dic['lastrowid']
                    thumbnail._generateThumbnails(real_path, doc_id)
        else:
            logging.info("thumbnail format not support: %s ... ", real_path)


    def get_new_thumbnail_id(self):
        out_dic = self.dbo_thumbnail.save()
        return out_dic

    def remove(self, doc_id):
        # todo: delete real file
        pass

        # delete database       
        out_dic = self.dbo_thumbnail.pk_delete(doc_id)
        return out_dic
