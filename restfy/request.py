import json
import mimetypes
from restfy.file import File


mime_types = {
    'multipart/form-data': 'form-data',
    'application/x-www-form-urlencoded': 'x-www-form-urlencoded',
    **{v: k[1:] for k, v in mimetypes.types_map.items()},
}


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
        self.connection = ''
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
        match key.lower():
            case 'content-type':
                if 'multipart/form-data' in value:
                    self.multipart = True
                    (content, boundary) = value.split(';')
                    self.type = content.strip()
                    self.boundary = boundary.replace('boundary=', '').strip()
                else:
                    self.type = mime_types.get(value, 'plain')
            case 'content-length':
                self.length = int(value)
            case 'origin':
                self.origin = value
                self.preflight = True if self.method == 'OPTIONS' else False
            case 'connection':
                self.connection = value.lower()
            case 'access-control-request-method':
                self.request_method = value
            case 'access-control-request-headers':
                self.request_headers = value

    def dict(self):
        return self.decode_data()

    def decode_data(self):
        if self.data:
            return self.data
        if self.body:
            if self.type == 'json':
                self.data = json.loads(self.body)
            elif self.type == 'form-data':
                self.data = self._process_form_data()
            elif self.type == 'x-www-form-urlencoded':
                self.data = self._url_decoded_data()
        return self.data

    def args(self):
        return self.query_args

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
