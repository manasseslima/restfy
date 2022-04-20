import asyncio
import datetime
import time
import inspect
from typing import List

from .http import Request, Response, AccessControl
from .router import Router, Route
from .middleware import Middleware


class Application:
    def __init__(
            self,
            title: str = 'Restfy',
            description: str = '',
            *,
            base_url: str = '',
            prepare_request_data: bool = True
    ):
        self.title = title
        self.description = description
        self.router = Router(base_url=base_url)
        self.cors = AccessControl()
        self.middlewares: List[Middleware] = []
        self.prepare_request_data = prepare_request_data

    def add_route(self, path, handle, method='GET'):
        self.router.add_route(path, handle, method)

    def register_router(self, path, router):
        self.router.register_router(path, router)

    async def handler(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        start = datetime.datetime.now()
        ini = time.time()
        data = await reader.readline()
        (method, url, version) = data.decode().replace('\n', '').split(' ')
        request = Request(method=method, version=version)
        request.prepare_url(url)
        try:
            while True:
                line = await reader.readline()
                header = line.decode()
                if header == '\r\n':
                    break
                header = header.replace('\r\n', '')
                splt = header.split(':', maxsplit=1)
                request.add_header(key=splt[0].strip(), value=splt[1].strip())
            if request.length:
                size = request.length
                content = b''
                while True:
                    content += await reader.read(size)
                    size = request.length - len(content)
                    if size == 0:
                        break
                request.body = content
            if request.preflight:
                response = Response(status=204)
                response.headers.update(self.cors.get_response_headers())
            else:
                if route := self.router.match(request.url, method):
                    request.app = self
                    response = await self.execute_middlewares(route, request)
                    if request.origin:
                        response.headers.update(self.cors.get_response_headers())
                else:
                    response = Response(status=404)
        except Exception as e:
            response = Response({'message': 'Internal server error', 'detail': str(e)}, status=500)
        writer.write(response.render())
        await writer.drain()
        writer.close()
        diff = time.time() - ini
        self.print_request(start, method, url, response, diff)

    async def execute_middlewares(self, route: Route, request: Request) -> Response:
        if self.middlewares:
            self.middlewares[-1].next = route
            response = await self.middlewares[0].exec(request)
        else:
            response = await route.exec(request)
        return response

    def register_middleware(self, middleware):
        instance = middleware()
        if self.middlewares:
            self.middlewares[-1].next = instance
        self.middlewares.append(instance)

    def get(self, path):
        return self.router.get(path)

    def post(self, path):
        return self.router.post(path)

    def put(self, path):
        return self.router.put(path)

    def delete(self, path):
        return self.router.delete(path)

    def patch(self, path):
        return self.router.patch(path)

    def options(self, path):
        return self.router.options(path)

    def head(self, path):
        return self.router.head(path)

    def print_request(self, start, method, url, response, diff):
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
        print(f'[{start.isoformat()}] {colors.get(method_color, colors["gray"])} {method} {url} '
              f'--> {colors.get(color_response, "")}{response.status}: {diff * 1000} ms\033[0m')

