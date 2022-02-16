import asyncio
from .http import Request, Response


class Application:
    def __init__(self):
        self.routers = {}

    async def handler(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        data = await reader.readline()
        (method, url, version) = data.decode().replace('\n', '').split(' ')
        request = Request(method=method, version=version)
        request.prepare_url(url)
        if request.url in self.routers and method in self.routers[request.url]:
            while True:
                data = await reader.readline()
                header = data.decode()
                if header == '\r\n':
                    break
                header = header.replace('\r\n', '')
                splt = header.split(':', maxsplit=1)
                request.add_header(key=splt[0].strip(), value=splt[1].strip())
            if request.length:
                size = request.length
                data = await reader.read(size)
                request.body = data
            response = await self.routers[request.url][request.method](request=request)
        else:
            response = Response(status=404)
        writer.write(response.render())
        await writer.drain()
        writer.close()

    def add_route(self, path, handle, method='GET'):
        if path in self.routers:
            self.routers[path][method.upper()] = handle
        else:
            self.routers[path] = {
                method.upper(): handle
            }

    async def run(self, host='0.0.0.0', port='7777'):
        print(f'RESTFY RUNNING ON {port}')
        server = await asyncio.start_server(self.handler, host, port)
        async with server:
            await server.serve_forever()
