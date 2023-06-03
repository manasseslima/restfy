import json
import mimetypes
from restfy.file import File


mime_types = {
    'multipart/form-data': 'form-data',
    'application/x-www-form-urlencoded': 'x-www-form-urlencoded',
    **{v: k[1:] for k, v in mimetypes.types_map.items()},
}


class AccessControl:
    allow_origin = '*'
    expose_headers = []
    max_age = 0.0
    allow_credentials = False
    allow_methods = []
    allow_headers = []

    def get_response_headers(self):
        headers = {
            'Access-Control-Allow-Origin': self.allow_origin,
        }
        if self.allow_methods:
            headers['Access-Control-Allow-Methods'] = ','.join(self.allow_methods)
        if self.allow_headers:
            headers['Access-Control-Allow-Headers'] = ','.join(self.allow_headers)
        if self.allow_credentials:
            headers['Access-Control-Allow-Credentials'] = self.allow_credentials
        if self.max_age:
            headers['Access-Control-Max-Age'] = self.max_age
        if self.expose_headers:
            headers['Access-Control-Expose-Headers'] = self.expose_headers
        return headers


class Request:
    def __init__(self, method: str = 'GET', version: str = '1.1'):
        self.app = None
        self.method = method
        self.url = ''
        self.port = ''
        self.version = version
        self.body = None
        self.type = ''
        self.query = ''
        self.length = 0
        self.headers = {}
        self.files = {}
        self.origin = ''
        self.request_method = ''
        self.request_headers = ''
        self.preflight = False
        self.multipart = False
        self.boundary = ''
        self.data = {}
        self.query_args: dict = {}
        self.params: dict = {}
        self.path_args: dict = {}
        self.vars: dict = {}

    def add_header(self, key, value):
        self.headers[key] = value
        if key == 'Content-Type':
            if 'multipart/form-data' in value:
                self.multipart = True
                (content, boundary) = value.split(';')
                self.type = content.strip()
                self.boundary = boundary.replace('boundary=', '').strip()
            else:
                self.type = mime_types.get(value, 'plain')
        elif key == 'Content-Length':
            self.length = int(value)
        elif key == 'Origin':
            self.origin = value
            self.preflight = True if self.method == 'OPTIONS' else False
        elif key == 'Access-Control-Request-Method':
            self.request_method = value
        elif key == 'Access-Control-Request-Headers':
            self.request_headers = value

    def dict(self):
        return self.decode_data()

    def decode_data(self):
        if self.body:
            if self.type == 'json':
                return json.loads(self.body)
            elif self.type == 'form-data':
                return self._process_form_data()
            elif self.type == 'x-www-form-urlencoded':
                return self._url_decoded_data()
        return {}

    def args(self):
        args = {}
        if self.query:
            pairs = self.query.split('&')
            for pair in pairs:
                (key, value) = pair.split('=')
                args[key] = value
        return args

    def prepare_data(self):
        self.data = self.decode_data()

    def _process_form_data(self):
        data = {}
        parts = self.body.split(f'--{self.boundary}'.encode())
        for part in parts:
            if not part or part == b'--\r\n':
                continue
            if b'filename=' in part:
                splt = part.split(b';', maxsplit=2)
                key = splt[1].decode().strip()[6:-1]
                (info, content) = splt[2].split(b'\r\n\r\n', maxsplit=1)
                (filename, kind) = info.decode().split('\r\n')
                filename = filename.strip()[10:-1]
                kind = kind.strip()[14:]
                file = File(name=filename, kind=kind, content=content)
                self.files[key] = file
            else:
                splt = part.split(b';')
                key, value = splt[1].split(b'\r\n\r\n')
                key = key.decode().replace('name=', '').strip()[1:-1]
                data[key] = value.strip().decode()
        return data

    def _url_decoded_data(self):
        data = {}
        pairs = self.body.decode().split('&')
        for pair in pairs:
            (key, value) = pair.split('=')
            data[key] = value
        return data
