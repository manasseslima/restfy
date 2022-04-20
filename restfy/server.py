import asyncio


class Server:
    def __init__(self, app=None, host='0.0.0.0', port=7777):
        self.app = app
        self.host = host
        self.port = port

    async def serve(self):
        print(f' {self.app.title.upper()} '.center(50 - len(self.app.title.upper()), '-'))
        print(f'\033[32mRESTFY\033[0m ON {self.port}')
        server = await asyncio.start_server(self.app.handler, self.host, self.port)
        async with server:
            await server.serve_forever()

    def run(self):
        asyncio.run(self.serve())
