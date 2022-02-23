import json


class Request:
    def __init__(self, method, version):
        self.method = method
        self.url = ''
        self.version = version
        self.body = None
        self.type = ''
        self.query = ''
        self.length = 0
        self.headers = {}
        self.files = []

    def add_header(self, key, value):
        self.headers[key] = value
        if key == 'Content-Type':
            self.type = value
        elif key == 'Content-Length':
            self.length = int(value)

    def dict(self):
        if self.body:
            return json.loads(self.body)
        return {}

    def args(self):
        args = {}
        if self.query:
            pairs = self.query.split('&')
            for pair in pairs:
                (key, value) = pair.split('=')
                args[key] = value
        return args
