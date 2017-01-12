# -*- coding: utf-8 -*-
import websocket
import ssl
import errno
from socket import error as socket_error
import json

class WSClient:
    version_string = u'v1.1'

    def version(self):
        return self.version_string

    def connect(self, api_hostname, api_reg_pattern, data=None, disconnect_after_recieve=True):
        http_code = 0
        json_obj = None

        is_connected = False
        ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        #api_hostname = "claim.dropboxlike.com"
        #api_hostname = "127.0.0.1"
        #api_reg_pattern = "1/ws_reg"
        api_url = "wss://%s:443/%s" % (api_hostname,api_reg_pattern)

        try:
            ws.connect(api_url)
            is_connected = True
        except socket_error as serr:
            if serr.errno != errno.ECONNREFUSED:
                # Not the error we are looking for, re-raise!
                raise serr
                pass
            else:
                #print "Can't connect to server."
                pass

        if is_connected:
            #print "Sent client info:", data
            #data = dict(action="reg",data={})
            ws.send(data)
            
            #print "Reeiving server pincode to mobile to input"
            while True:
                result = None
                try:
                    result =  ws.recv()
                    #print "Received '%s'" % result
                except websocket._exceptions.WebSocketConnectionClosedException:
                    #print "Server close connection"
                    break
                except KeyboardInterrupt:
                    break

                if result:
                    json_obj = None
                    try :
                        json_obj = json.loads(result)
                        http_code = 200
                        if 'error' in json_obj:
                            http_code = 400
                    except ValueError as err:  # includes simplejson.decoder.JSONDecodeError
                        #print('except:%s' % (str(err)))
                        pass
                    except Exception as err:
                        #print('except:%s' % (str(err)))
                        pass

                    #print "get server response, but don't know break connection or not."
                    if disconnect_after_recieve:
                        break
                else:
                    # server close connection.
                    break
            
        return http_code, json_obj
