import json
from .application import Application, Response


class Client:
    def __init__(self, app: Application):
        self.app = app

    async def request(
            self,
            method: str,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        headers = headers or {}
        req = self.app.generate_request(url=url, method=method, version='http/1.1')
        for k, v in headers.items():
            req.add_header(k, v)
        content_type = req.headers.get('Content-Type', '')
        if not content_type:
            if isinstance(data, bytes):
                raise Exception(f'A content type need to be set on headers')
            req.body = json.dumps(data).encode()
            req.add_header('Content-Type', 'application/json')
            req.add_header('Content-Length', len(req.body))
        else:
            if content_type == 'application/json' and not isinstance(data, bytes):
                req.body = json.dumps(data).encode()
                req.add_header('Content-Length', len(req.body))
        res = await self.app.execute_handler(req)
        res.render()
        return res

    async def get(
            self,
            url: str,
            headers: dict = None
    ) -> Response:
        return await self.request('GET', url, headers=headers)

    async def post(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('POST', url, data, headers)

    async def put(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('PUT', url, data, headers)

    async def delete(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('DELETE', url, data, headers)

    async def patch(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('PATCH', url, data, headers)

    async def options(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('OPTIONS', url, data, headers)

    async def header(
            self,
            url: str,
            data: ... = None,
            headers: dict = None
    ) -> Response:
        return await self.request('HEADER', url, data, headers)
