from handlers import BaseHandler

class HelloHandler(BaseHandler):
    def get(self):
        #self.set_header('Content-Type','application/json')
        self.render('hello.html', word='Welcome to use Augusta Web Service!')

