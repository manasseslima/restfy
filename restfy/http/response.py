import json

status_title = {
    200: 'OK',
    400: 'ERRO',
    404: 'NOT FOUND',
}


class Response:
    def __init__(self, data='', status=200):
        self.version = 'HTTP/1.1'
        self.status = status
        self.headers = {
            'Content-Type': 'text/plain'
        }
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
