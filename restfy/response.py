import json
import datetime
import decimal
from typing import Any

status_title = {
    101: 'Switching Protocols',
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


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, "dict"):
            return self.default(o.dict())
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, decimal.Decimal):
            return float(o)
        return o


class Response:
    def __init__(
            self,
            data: Any = None,
            status: int = 200,
            *,
            content_type: str = '',
            headers: dict = None
    ):
        self.version = 'HTTP/1.1'
        self.status = status
        self.data = data if status != 204 else None
        self.headers = {}
        self.content_type = content_type
        self._prepare_headers(headers)
        self.content = b''
        self.text = ''

    def render(self) -> bytes:
        title = status_title.get(self.status, 'STATUS WITHOUT TITLE')
        headers = '\r\n'.join([f"{k}:{v}" for k, v in self.headers.items()])
        body = self.data
        content = f'{self.version} {self.status} {title}\r\n{headers}\r\n\r\n'
        if body:
            content = f'{content}{body}'
            self.content = body.encode()
        return content.encode()

    def parser(self, model: Any = None):
        res = json.loads(self.data)
        if model:
            res = model(**res)
        return res

    def _prepare_headers(self, headers):
        if not headers:
            headers = {}
        if self.data is None:
            self.data = ''
        if self.content_type:
            self.headers['Content-Type'] = self.content_type
        if isinstance(self.data, dict) or isinstance(self.data, list):
            self.data = json.dumps(self.data, cls=JSONEncoder)
            self.headers['Content-Type'] = 'application/json'
        elif isinstance(self.data, bytes):
            self._identify_binary_data()
        elif isinstance(self.data, str):
            self.headers['Content-Type'] = 'text/plain'
        self.headers['Content-Length'] = len(self.data)
        self.headers.update(headers)

    def _identify_binary_data(self):
        if self.data[1:4] == 'PDF':
            self.headers['Content-Type'] = 'application/pdf'
