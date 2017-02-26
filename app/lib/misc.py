#!/usr/bin/env python
#fileencoding=utf-8

import random
import string
import hashlib
import time
import signal
from uuid import uuid4

def rand_abc(desired_len):
    sr = random.SystemRandom()
    printable = ['A','B','C','E','F','H','M','N','P','R','T','W','X','Y']
    printable_len = len(printable)
    chars = [printable[sr.randint(0, printable_len - 1)] for _ in
             range(desired_len)]
    return ''.join(chars)

def rand_number(desired_len):
    sr = random.SystemRandom()
    printable = string.digits
    printable_len = len(printable)
    chars = [printable[sr.randint(0, printable_len - 1)] for _ in
             range(desired_len)]
    return ''.join(chars)

def rand_string(desired_len):
    sr = random.SystemRandom()
    printable = string.letters + string.digits
    printable_len = len(printable)
    chars = [printable[sr.randint(0, printable_len - 1)] for _ in
             range(desired_len)]
    return ''.join(chars)

def sha1_hash(value):
    sha1 = hashlib.sha1()
    sha1.update(value)
    digest = sha1.hexdigest()
    return digest

def md5_hash(value):
    data = hashlib.md5()
    data.update(value)
    digest = data.hexdigest()
    return digest

def md5_file(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_mac():
    from uuid import getnode as get_mac
    mac = get_mac()
    mac_formated = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    return mac_formated

def get_ip_address():
    import socket
    ip = None
    (hostname, aliaslist, ipaddrlist) = socket.gethostbyname_ex(socket.gethostname())

    localIp = socket.gethostbyname(socket.gethostname())
    if localIp[:4] == "127.":
        ipaddrlist.remove(localIp)

    if len(ipaddrlist) > 0:
        ip = ipaddrlist[len(ipaddrlist)-1]

    if len(ipaddrlist) > 1:
        import netifaces as ni
        interface_arr = ni.interfaces()
        if 'vboxnet0' in interface_arr:
            # {18: [{'addr': '0a:00:27:00:00:00'}], 2: [{'broadcast': '192.168.56.255', 'addr': '192.168.56.1'}]}
            ip = ni.ifaddresses('vboxnet0')[2][0]['addr']
            ipaddrlist.remove(ip)
    #print "ipaddrlist", ipaddrlist
    if len(ipaddrlist) > 0:
        ip = ipaddrlist[len(ipaddrlist)-1]
    return ip

def install_tornado_shutdown_handler(ioloop, server, logger=None):
    # see https://gist.github.com/mywaiting/4643396 for more detail
    if logger is None:
        import logging
        logger = logging

    def _sig_handler(sig, frame):
        #logger.info("Signal %s received. Preparing to stop server.", sig)
        ioloop.add_callback(shutdown)

    def shutdown():
        logger.info("Stopping http server...")
        server.stop()

        MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
        #logger.info("Will shutdown in %s seconds", MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

        def stop_loop():
            now = time.time()
            if now < deadline and (ioloop._callbacks or ioloop._timeouts):
                ioloop.add_timeout(now + 1, stop_loop)
                logger.debug("Waiting for callbacks and timeouts in IOLoop...")
            else:
                ioloop.stop()
                #logger.info("Server is shutdown")

        stop_loop()

    signal.signal(signal.SIGTERM, _sig_handler)
    signal.signal(signal.SIGINT, _sig_handler)
