import asyncio
import datetime
import time
import uuid
from typing import List
from .request import Request, AccessControl
from .response import Response
from .router import Router, Route
from .middleware import Middleware
from .connection import Connection, H1Connection, H2Connection


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
        self.connections: dict[uuid.UUID, Connection] = {}

    def add_route(self, path, handle, method='GET'):
        self.router.add_route(path, handle, method)

    def register_router(self, path, router):
        self.router.register_router(path, router)

    async def handler(
            self,
            reader: asyncio.streams.StreamReader,
            writer: asyncio.streams.StreamWriter
    ):
        data = await reader.readline()
        if data == b'PRI * HTTP/2.0\r\n':
            conn = H2Connection(reader=reader, writer=writer)
        else:
            conn = H1Connection(reader=reader, writer=writer)
        conn.middlewares = self.middlewares
        conn.router = self.router
        conn.cors = self.cors
        conn.prepare_request_data = self.prepare_request_data
        conn.app = self
        self.connections[conn.id] = conn
        await conn.handler(data)

    def connection_close(self):
        ...

    def register_middleware(self, middleware: type[Middleware]):
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

    def websocket(self, path):
        return self.router.websocket(path)
