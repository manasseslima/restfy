import json
import datetime
import decimal
from typing import Any
from restfy.background import BackgroundTask, BackgroundTasks

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
            headers: dict = None,
            background=None,
    ):
        self.version = 'HTTP/1.1'
        self.status = status
        self.data = data if status != 204 else None
        self.headers = {}
        self.content_type = content_type
        if isinstance(background, BackgroundTask):
            _bg = BackgroundTasks()
            _bg._tasks.append(background)
            self.background = _bg
        else:
            self.background = background
        self.content = b''
        self.text = ''
        self.body = b''
        self.cookies: list[str] = []
        self._prepare_headers(headers)

    def render(self) -> bytes:
        title = status_title.get(self.status, 'STATUS WITHOUT TITLE')
        header_lines = '\r\n'.join([f"{k}:{v}" for k, v in self.headers.items()])
        cookie_lines = ''.join([f"\r\nSet-Cookie:{c}" for c in self.cookies])
        return f'{self.version} {self.status} {title}\r\n{header_lines}{cookie_lines}\r\n\r\n'.encode() + self.body

    def set_cookie(
            self,
            name: str,
            value: str,
            *,
            path: str = '/',
            domain: str = '',
            max_age: int = None,
            expires: str = '',
            httponly: bool = False,
            secure: bool = False,
            samesite: str = 'lax',
    ) -> None:
        parts = [f"{name}={value}"]
        if path:
            parts.append(f"Path={path}")
        if domain:
            parts.append(f"Domain={domain}")
        if max_age is not None:
            parts.append(f"Max-Age={max_age}")
        if expires:
            parts.append(f"Expires={expires}")
        if samesite:
            parts.append(f"SameSite={samesite.capitalize()}")
        if httponly:
            parts.append("HttpOnly")
        if secure:
            parts.append("Secure")
        self.cookies.append('; '.join(parts))

    def delete_cookie(self, name: str, *, path: str = '/', domain: str = '') -> None:
        self.set_cookie(
            name, '',
            path=path,
            domain=domain,
            max_age=0,
            expires='Thu, 01 Jan 1970 00:00:00 GMT',
            samesite='',
        )

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
        if isinstance(self.data, dict) or isinstance(self.data, list):
            self.data = json.dumps(self.data, cls=JSONEncoder)
            if not self.content_type:
                self.headers['Content-Type'] = 'application/json'
        elif isinstance(self.data, bytes):
            if not self.content_type:
                self._identify_binary_data()
        elif isinstance(self.data, str):
            if not self.content_type:
                self.headers['Content-Type'] = 'text/plain'
        if self.content_type:
            self.headers['Content-Type'] = self.content_type
        self.body = self.data if isinstance(self.data, bytes) else self.data.encode()
        self.headers['Content-Length'] = len(self.body)
        self.headers.update(headers)

    def _identify_binary_data(self):
        if self.data[:4] == b'%PDF':
            self.headers['Content-Type'] = 'application/pdf'
        else:
            self.headers['Content-Type'] = 'application/octet-stream'
