import asyncio
import datetime
import enum
import queue
import time
import uuid
from collections import deque

from restfy.request import Request, AccessControl
from restfy.response import Response
from restfy.middleware import Middleware
from restfy.websocket import prepare_websocket
from restfy.router import Router, Route
from restfy.connection import frame


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
            reader: asyncio.StreamReader | None,
            writer: asyncio.StreamWriter | None,
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
        self.dynamic_table = deque()

    @staticmethod
    def get_frame(frame_header: bytes, connection: 'H2Connection'):
        frm = {
            0: frame.DataFrame,
            1: frame.HeaderFrame,
            2: frame.PriorityFrame,
            3: frame.RSTStreamFrame,
            4: frame.SettingFrame,
            5: frame.PushPromisseFrame,
            6: frame.PingFrame,
            7: frame.GoawayFrame,
            8: frame.WindowUpdateFrame,
            9: frame.ContinuationFrame,
        }.get(frame_header[3], frame.Frame)(
            length=frame_header[:3],
            flags=frame_header[4],
            stream=frame_header[5:],
            connection=connection
        )
        return frm

    def add_dynamic_table_element(self, value: str):
        self.dynamic_table.appendleft(value)

    def get_dynamic_table_element(self, key):
        return self.dynamic_table[key - 61]

    async def handler(self, data: bytes):
        data += await self.reader.read(8)
        streams = {}
        while True:
            frame_header = await self.reader.read(9)
            fme = self.get_frame(frame_header, self)
            chunk = await self.reader.read(fme.length)
            fme.set_payload(chunk)
            if fme.stream not in streams:
                streams[fme.stream] = {'frames': {}}
            streams[fme.stream]['frames'][fme.id] = fme
            if isinstance(fme, frame.HeaderFrame):
                headers = fme.payload
                method = headers.pop('method')
                version = '2'
                url = headers['path']
                request = self.generate_request(url=url, method=method, version=version)
                for k, v in headers.items():
                    request.add_header(k, v)
                streams[fme.stream]['request'] = request
                if method == 'GET' and fme.end_headers:
                    await self.process_response(request, stream=fme.stream)
            if isinstance(fme, frame.DataFrame):
                request = streams[fme.stream]['request']
                request.body = fme.payload
                if fme.end_stream:
                    await self.process_response(request, stream=fme.stream)
            if isinstance(fme, frame.RSTStreamFrame):
                break
        ...

    async def process_response(self, request: Request, stream: int):
        response: Response = await self.execute_handler(request=request)
        self.generate_header_frame_block(response=response, stream=stream)
        self.generate_data_frame_block(response=response, stream=stream)
        await self.writer.drain()
        diff = time.time_ns() - self.ini
        self.print_request(self.start, request.method, request.url, response, diff)

    def generate_data_frame_block(self, response: Response, stream: int) -> bytes:
        data = response.data.encode()
        data_fme = frame.DataFrame(
            length=len(data).to_bytes(3, byteorder='big', signed=False),
            flags=0b00000001,
            stream=stream.to_bytes(4, byteorder='big', signed=False),
            connection=self
        )
        data_fme.payload = data
        block = data_fme.generate()
        self.writer.write(block)

    def generate_header_frame_block(self, response: Response, stream: int) -> bytes:
        fme = frame.HeaderFrame(
            length=b'\x00\x00\x00',
            flags=0b00000100,
            stream=stream.to_bytes(4, byteorder='big', signed=False),
            connection=self
        )
        headers = response.headers
        headers['status'] = response.status
        fme.payload = headers
        block = fme.generate()
        self.writer.write(block)


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
