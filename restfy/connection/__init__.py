import asyncio
import datetime
import enum
import time
import uuid

from restfy.request import Request, AccessControl
from restfy.response import Response
from restfy.middleware import Middleware
from restfy.websocket import prepare_websocket
from restfy.router import Router, Route
from .frame import Frame, SettingFrame


class ConnectionStatus(enum.Enum):
    OPENING = 0
    CLOSING = 1
    WAITING = 2
    OPENED = 3
    IDLE = 4


class Connection:
    def __init__(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ):
        self.id: uuid.UUID = uuid.uuid4()
        self.start = datetime.datetime.now()
        self.ini = time.time_ns()
        self.reader = reader
        self.writer = writer
        self.cors: AccessControl = AccessControl()
        self.prepare_request_data: bool = True
        self.status: ConnectionStatus = ConnectionStatus.OPENED
        self.middlewares: list[Middleware] = []
        self.router: Router | None = None
        self.app = None

    async def handler(self, data: bytes):
        ...

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
        del self.app.connections[self.id]

    async def execute_handler(self, request: Request):
        if route := self.router.match(request.url, request.method):
            response = await self.execute_middlewares(route, request)
            if request.origin:
                response.headers.update(self.cors.get_response_headers())
            if route.is_websocket:
                prepare_websocket(request=request, response=response)
        else:
            response = Response(status=404)
        return response

    async def execute_middlewares(self, route: Route, request: Request) -> Response:
        if self.middlewares:
            self.middlewares[-1].next = route
            response = await self.middlewares[0].exec(request)
        else:
            response = await route.exec(request)
        return response

    def generate_request(
            self,
            url: str,
            method: str,
            version: str
    ) -> Request:
        request = Request(method=method, version=version)
        request.app = self.app
        splt = url.split('?')
        path, query = splt[0], splt[1] if len(splt) > 1 else ''
        request.url = path
        request.query = query
        args = self.extract_arguments(query=query)
        request.query_args = args
        request.params = {**args}
        return request

    def extract_arguments(self, query):
        ret = {}
        if query:
            pairs = query.split('&')
            for pair in pairs:
                (key, value) = tuple(pair.split('='))
                ret[key] = self.argument_decode(value)
        return ret

    @staticmethod
    def argument_decode(value):
        return value

    @staticmethod
    def print_request(start, method, url, response, diff):
        colors = {
            'black': '\033[30m',
            'red': '\033[31m',
            'green': '\033[32m',
            'orange': '\033[33m',
            'blue': '\033[34m',
            'pink': '\033[35m',
            'cian': '\033[36m',
            'gray': '\033[37m',
            'white': '\033[38m',
        }
        if response.status >= 400:
            color_response = 'red'
        else:
            color_response = 'blue'
        methods_color = {
            'GET': 'green',
            'POST': 'blue',
            'PUT': 'orange',
            'DELETE': 'red',
        }
        method_color = methods_color.get(method, '')
        print(f'[{start.isoformat()[:-3]}]{colors.get(method_color, colors["gray"])} {method} {url} '
              f'--> {colors.get(color_response, "")}{response.status}: {diff / (1_000_000)} ms\033[0m')


class H2Connection(Connection):
    def __init__(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ):
        super().__init__(reader=reader, writer=writer)
        self.frames = {}

    async def handler(self, data: bytes):
        data += await self.reader.read(8)
        frame_header = await self.reader.read(9)
        typo = frame_header[3]
        match typo:
            case 4: frame_cls = SettingFrame
            case _: frame_cls = Frame
        frame = frame_cls(length=frame_header[:3], flags=frame_header[4], identifier=frame_header[5:])
        while True:
            chunk = await self.reader.read(4000)
            chunk = frame.set_payload(chunk)
            data += chunk


class H1Connection(Connection):
    async def handler(self, data: bytes):
        (method, url, version) = data.decode().replace('\n', '').split(' ')
        request = self.generate_request(url=url, method=method, version=version)
        try:
            while True:
                line = await self.reader.readline()
                header = line.decode()
                if header == '\r\n':
                    break
                header = header.replace('\r\n', '')
                splt = header.split(':', maxsplit=1)
                request.add_header(key=splt[0].strip(), value=splt[1].strip())
            if request.length:
                length = request.length
                size = length if length <= 1000 else 1000
                content = b''
                while True:
                    content += await self.reader.read(size)
                    length -= size
                    if length == 0:
                        break
                    size = length if length <= 1000 else 1000
                request.body = content
            if request.preflight:
                response = Response(status=204)
                response.headers.update(self.cors.get_response_headers())
            else:
                response = await self.execute_handler(request=request)
        except Exception as e:
            response = Response({'message': 'Internal Server Error', 'detail': str(e)}, status=500)
        block = response.render()
        self.writer.write(block)
        await self.writer.drain()
        await self.close()
        diff = time.time_ns() - self.ini
        self.print_request(self.start, method, url, response, diff)
