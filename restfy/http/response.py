import json

status_title = {
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLIT',
    410: 'GONE',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPORTED'
}


class Response:
    def __init__(self, data='', status=200, headers=None):
        self.version = 'HTTP/1.1'
        self.status = status
        self.headers = {
            'Content-Type': 'text/plain'
        }
        if headers:
            self.headers.update(headers)
        self.data = None
        if isinstance(data, dict) or isinstance(data, list):
            self.data = json.dumps(data)
            self.headers['Content-Type'] = 'application/json'
            self.headers['Content-length'] = len(self.data)
        elif isinstance(data, bytes):
            self.data = data
        else:
            self.data = data

    def render(self):
        title = status_title.get(self.status, 'STATUS WITHOUT TITLE')
        headers = '\r\n'.join([f"{k}:{v}" for k, v in self.headers.items()])
        body = self.data
        content = f'{self.version} {self.status} {title}\r\n{headers}\r\n\r\n{body}'
        return content.encode()
