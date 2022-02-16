import json


class Request:
    def __init__(self, method, version):
        self.method = method
        self.url = ''
        self.args = {}
        self.version = version
        self.body = None
        self.type = ''
        self.length = 0
        self.headers = {}
        self.files = []

    def add_header(self, key, value):
        self.headers[key] = value
        if key == 'Content-Type':
            self.type = value
        elif key == 'Content-Length':
            self.length = int(value)

    def prepare_url(self, url):
        if '?' in url:
            (path, query) = url.split('?')
        else:
            path = url
            query = ''
        self.url = path
        if query:
            pairs = query.split('&')
            for pair in pairs:
                (key, value) = pair.split('=')
                self.args[key] = value

    def json(self):
        if self.body:
            return json.loads(self.body)
        return {}
