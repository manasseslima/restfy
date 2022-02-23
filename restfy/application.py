import asyncio
import datetime
from .http import Request, Response
from .router import Router, Handler


class Application:
    def __init__(self, base_url=''):
        self.router = Router(base_url=base_url)

    def add_route(self, path, handle, method='GET'):
        self.router.add_route(path, Handler(handle), method)

    async def handler(self, reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter):
        data = await reader.readline()
        (method, url, version) = data.decode().replace('\n', '').split(' ')
        print(f"[{datetime.datetime.now().isoformat()}] {method} {url}")
        request = Request(method=method, version=version)
        self.prepare_url(url, request)
        try:
            if route := self.router.match(request.url, method):
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
                response = await route.exec(request)
            else:
                response = Response(status=404)
        except Exception as e:
            response = Response({'message': 'Internal server error', 'detail': str(e)}, status=500)
        writer.write(response.render())
        await writer.drain()
        writer.close()

    def prepare_url(self, url, request):
        if '?' in url:
            (path, query) = url.split('?')
        else:
            path = url
            query = ''
        request.url = path
        request.query = query


