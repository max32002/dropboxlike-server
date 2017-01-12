import json
import time
import uuid

def json_dump(_obj, _ascii = False):
    return json.dumps(_obj, ensure_ascii = _ascii)

def get_timestamp():
    return int(round(time.time()*1000))
    
def get_uuid():
    return str(uuid.uuid4())

def get_token():
    return str(uuid.uuid4().hex)

