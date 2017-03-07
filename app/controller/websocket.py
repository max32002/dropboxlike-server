#!/usr/bin/env python
#encoding=utf-8

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
'''
This is a simple Websocket Echo server that uses the Tornado websocket handler.
Please run `pip install tornado` with python of version 2.7.9 or greater to install tornado.
This program will echo back the reverse of whatever it recieves.
Messages are output to the terminal for debuggin purposes. 
''' 

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print 'new websocket connection'
      
    def on_message(self, message):
        print 'message received:  %s' % message
        # Reverse Message and send it back
        #print 'sending back message: %s' % message[::-1]
        #self.write_message(message[::-1])
        #self.write_message({"action":"ok"})
        #self.write_message({"action":"connected"})
 
    def on_close(self):
        print 'websocket connection closed'
 
    def check_origin(self, origin):
        return True
