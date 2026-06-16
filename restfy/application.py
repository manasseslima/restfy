import asyncio
import datetime
import time
import uuid
from typing import List
from .cors import CORSConfig
from .request import Request
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
            prepare_request_data: bool = True,
            cors: CORSConfig = None,
    ):
        self.title = title
        self.description = description
        self.router = Router(base_url=base_url)
        self.cors: CORSConfig = cors or CORSConfig()
        self.middlewares: List[Middleware] = []
        self.prepare_request_data = prepare_request_data
        self.connections: dict[uuid.UUID, Connection] = {}
        self.error_handlers: dict[int, callable] = {}
        self.exception_handlers: dict[type, callable] = {}
        self.static_mounts: dict[str, str] = {}

    def configure_cors(
            self,
            *,
            allow_origins: list[str] | str = '*',
            allow_methods: list[str] = None,
            allow_headers: list[str] = None,
            allow_credentials: bool = False,
            max_age: int = 0,
            expose_headers: list[str] = None,
    ):
        self.cors = CORSConfig(
            allow_origins=allow_origins,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            allow_credentials=allow_credentials,
            max_age=max_age,
            expose_headers=expose_headers,
        )

    def on_error(self, status: int):
        """Register a handler for a specific HTTP status code."""
        def decorator(func):
            self.error_handlers[status] = func
            return func
        return decorator

    def on_exception(self, exc_type: type):
        """Register a handler for a specific exception type (MRO-aware)."""
        def decorator(func):
            self.exception_handlers[exc_type] = func
            return func
        return decorator

    def get_exception_handler(self, exc_type: type):
        for cls in exc_type.__mro__:
            if cls in self.exception_handlers:
                return self.exception_handlers[cls]
        return None

    def mount_static(self, path: str, *, directory: str):
        """Serve static files from *directory* under the URL *path* prefix."""
        self.static_mounts[path.rstrip('/')] = directory

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
