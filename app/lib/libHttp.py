# -*- coding: utf-8 -*-
import json
import urllib2
import ssl

class Http:
    version_string = u'v1.2'

    def version(self):
        return self.version_string

    def get_http_response(self, url):
        #read_body_flag = False
        read_body_flag = True
        headers = None
        return self.get_http_response_core(url, read_body_flag=read_body_flag, headers=headers)

    def get_http_response_core(self, url, read_body_flag=True, data=None, headers=None):
        return_html = ''
        return_code = 0
        req = None
        response = None
        #is_debug = True
        is_debug = False
        
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            #data_encoded = None
            #if not data is None:
                #data_encoded = urllib.urlencode(data)
            if headers is None:
                req = urllib2.Request(url, data=data)
            else:
                req = urllib2.Request(url, data=data, headers=headers)
            #req.add_header('foo', 'bar')
            #req.addheaders = [('User-agent', 'Mozilla/5.0')]
            
            # This restores the same behavior as before.
            #context = ssl._create_unverified_context()

            response=urllib2.urlopen(req)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                #HTTPError and URLError all have reason attribute.
                if is_debug:
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                    print 'url: ', url
                #return_html = e.reason
                if hasattr(e, 'code'):
                    return_code = e.code
                else:
                    return_code = 0
            elif hasattr(e, 'code'):
                #Only HTTPError has code attribute.
                if is_debug:
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                return_code = e.code

            #print "return_code:%d" % return_code
            if return_code in range(200,500):
                if read_body_flag:
                    return_html = e.read()
        else:
            # everything is fine
            return_code = response.getcode()

            # for performance, not return url's body.
            if read_body_flag:
                return_html = response.read()

            #if response.getcode()== 200:
                #return (response.read(), response.getcode())
                #return ('', response.getcode())
            #else:
                #return ('', response.getcode())
        return (return_html, return_code)
