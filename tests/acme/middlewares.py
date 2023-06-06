from restfy import Response, Middleware


class SomeMiddleware(Middleware):
    async def exec(self, request) -> Response:
        request.headers['Acme-Transaction-Id'] = '123456789'
        response = await self.forward(request=request)
        response.headers['Acme-Transaction-Id'] = '123456789'
        return response


class AnotherMiddleware(Middleware):
    async def exec(self, request) -> Response:
        request.headers['Acme-Session-Id'] = '987654321'
        response = await self.forward(request=request)
        response.headers['Acme-Session-Id'] = '987654321'
        return response
