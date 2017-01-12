from tornado.options import options
import logging
from app.dbo.metadata import DboMetadata
from app.lib import utils
import json

class MetaManager():
    '''!Metadata API Controller'''
    dbo_metadata = None
    account = None

    def __init__(self, metadata_conn, account):
        self.account = account
        self.dbo_metadata = DboMetadata(metadata_conn)

    def query(self, path):
        ret_dict = None
        if path != '':
            ret_dict = self.dbo_metadata.get_path(path)
        else:
            ret_dict = [self.root_dict()]
        return ret_dict

    def query_formated(self, path):
        metadata_dic = {}
        dic_current = self.query(path)
        #logging.info('dic_current:%s' % (dic_current))
        if len(dic_current) > 0:
            metadata_dic = self.convert_dict(dic_current[0])
            dic_children = self.dbo_metadata.get_contents(path)
            #print 'dic_children:%s' % (dic_children)
            contents = []

            # for small case used.
            for item in dic_children:
                contents.append(self.convert_dict(item))
            metadata_dic['contents']=contents
            #print 'dic_current:%s' % (metadata_dic)
            #self.write(metadata_dic)

            # for big data used. (but, seems speed the same.)
            '''
            metadata_dic['contents']=contents
            delimiter = '\"contents\": ['
            #body = "{}".format(metadata_dic)
            body = json.dumps(metadata_dic)
            body_item = body.split(delimiter)
            self.write(body_item[0]+delimiter)
            dic_children_count = len(dic_children)
            if dic_children_count > 0:
                iPos = 0
                for item in dic_children:
                    iPos += 1
                    self.write(json.dumps(self.convert_dict(item)))
                    if iPos < dic_children_count:
                        self.write(",")
            self.write(body_item[1])
            '''
        else:
            pass
            #self.set_status(404)
            #self.write(dict(error_msg='path not found.',error_code=123))
        #metadata_dic = self.convert_dict()

        return metadata_dic

    def root_dict(self):
        in_dic = {}
        in_dic['path'] = ''
        in_dic['comment'] = 0
        in_dic['shared_flag'] = 0
        in_dic['hash'] = ''
        in_dic['permission'] = ''
        in_dic['rev'] = ''
        in_dic['bytes'] = 0
        in_dic['mtime'] = ''
        in_dic['lock'] = 0
        in_dic['is_dir'] = 1
        in_dic['favorite'] = 0
        in_dic['modify_time'] = utils.get_timestamp()
        in_dic['editor'] = self.account
        in_dic['owner'] = self.account
        return in_dic

    def convert_dict(self, tmp_dict):
        in_dic = {}
        in_dic['path'] = '/' + tmp_dict['path']
        in_dic['comment'] = tmp_dict['comment']
        in_dic['shared_flag'] = (True if tmp_dict['shared_flag']==1 else False)
        #in_dic['hash'] = tmp_dict['hash']
        in_dic['hash'] = '135d4855eadffd0fd4f4dadaecf942b7'
        #in_dic['permission'] = tmp_dict['permission']
        in_dic['permission'] = {"write": True}
        #in_dic['rev'] = tmp_dict['rev']
        in_dic['rev'] = '135d4855eadffd0fd4f4dadaecf942b7'
        in_dic['store_bytes'] = tmp_dict['bytes']
        in_dic['bytes'] = tmp_dict['bytes']
        in_dic['size'] = str(tmp_dict['bytes']) + " KB"
        in_dic['store_size'] = str(tmp_dict['bytes']) + " KB"
        in_dic['mtime'] = (tmp_dict['mtime'] if len(tmp_dict['mtime'])>0 else None)
        in_dic['lock'] = (True if tmp_dict['lock']==1 else False)
        in_dic['is_dir'] = (True if tmp_dict['is_dir']==1 else False)
        in_dic['favorite'] = (True if tmp_dict['favorite']==1 else False)
        in_dic['modified'] = tmp_dict['modify_time']
        in_dic['owner'] = tmp_dict['owner']

        # for FC client
        in_dic['root'] = 'File Cruiser'
        in_dic['compress'] = False
        in_dic['encrypt'] = False
        in_dic['thumb_exists'] = True
        in_dic['icon'] = ( 'folder_public' if tmp_dict['is_dir']==1 else "page_white_acrobat")
        return in_dic

    def add(self, path, bytes=0, rev='', mtime='', is_dir=0):
        in_dic = {}
        in_dic['path'] = path
        in_dic['comment'] = 0
        in_dic['shared_flag'] = 0
        in_dic['hash'] = utils.get_uuid()
        in_dic['permission'] = ''
        in_dic['rev'] = rev
        in_dic['bytes'] = bytes
        in_dic['mtime'] = mtime
        in_dic['lock'] = 0
        in_dic['is_dir'] = is_dir
        in_dic['favorite'] = 0
        in_dic['editor'] = self.account
        in_dic['owner'] = self.account
        return self.dbo_metadata.insert(in_dic)

    def move(self, from_path, to_path, comment=None, shared_flag=None, permission=None, rev=None, bytes=None, mtime=None, lock=None, is_dir=None, favorite=None):
        in_dic = {}
        in_dic['old_path'] = from_path
        in_dic['path'] = to_path
        if not comment is None:
            in_dic['comment'] = comment 
        if not shared_flag is None:
            in_dic['shared_flag'] = shared_flag 
        #if not hash is None:
        #    in_dic['hash'] = '' 
        if not permission is None:
            in_dic['permission'] = permission 
        if not rev is None:
            in_dic['rev'] = rev 
        if not bytes is None:
            in_dic['bytes'] = bytes 
        if not mtime is None:
            in_dic['mtime'] = mtime 
        if not lock is None:
            in_dic['lock'] = lock 
        if not is_dir is None:
            in_dic['is_dir'] = is_dir
        if not favorite is None:
            in_dic['favorite'] = favorite 
        in_dic['editor'] = self.account
        return self.dbo_metadata.update(in_dic)

    def copy(self, from_path, to_path):
        in_dic = {}
        in_dic['old_path'] = from_path
        in_dic['path'] = to_path
        in_dic['editor'] = self.account
        return self.dbo_metadata.copy(in_dic)


    def remove(self, path):
        # todo: 
        #   check permission...
        # 

        in_dic = {}
        in_dic['path'] = path
        return self.dbo_metadata.delete(in_dic)

