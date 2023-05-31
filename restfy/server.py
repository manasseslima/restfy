import asyncio
import ssl


class Server:
    def __init__(
            self,
            app=None,
            *,
            host: str = '0.0.0.0',
            port: str = 7777,
            ssl_crt: str = '',
            ssl_key: str = ''
    ):
        self.app = app
        self.host = host
        self.port = port
        self.ssl_crt = ssl_crt
        self.ssl_key = ssl_key

    async def serve(self):
        print(f' {self.app.title.upper()} '.center(50 - len(self.app.title.upper()), '-'))
        print(f'\033[32mRESTFY\033[0m ON {self.port}')
        if self.ssl_crt and self.ssl_key:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.load_cert_chain(self.ssl_crt, self.ssl_key)
        else:
            context = None
        server = await asyncio.start_server(
            self.app.handler,
            self.host,
            self.port,
            ssl=context
        )
        async with server:
            await server.serve_forever()

    def run(self):
        asyncio.run(self.serve())
