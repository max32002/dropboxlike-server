import json
import time
import uuid
import mimetypes


def json_dump(_obj, _ascii = False):
    '''!dump dict to json object
    @param _obj dict to json
    @retval Object json object
    '''
    return json.dumps(_obj, ensure_ascii = _ascii)

def guess_mimetype(target):
    guessed_type, _junk = mimetypes.guess_type(target)
    if not guessed_type :
        return ''
    return guessed_type

def get_timestamp():
    '''!get current timestamp(ms)
    @retval Int current timestamp
    '''
    return int(round(time.time()*1000))
    
def get_uuid():
    '''!get uuid
    @retval String uuid
    '''
    return str(uuid.uuid4())

def get_token():
    '''!get token
    @retval String token
    '''
    return str(uuid.uuid4().hex)

def get_docid():
    '''!get docid
    @retval String docid
    '''
    return str(uuid.uuid4().hex)[2:] + "-" + get_token()
