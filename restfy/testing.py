from .application import Application, Response, Request


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
        req = Request(method=method)
        req.url = url
        req.app = self.app
        req.headers = headers or {}
        req.body = data or b''
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
