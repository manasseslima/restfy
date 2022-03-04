from .http import Request, Response


class Middleware:
    def __init__(self):
        self.next = None

    async def exec(self, request) -> Response:
        response = await self.forward(request)
        return response

    async def forward(self, request) -> Response:
        response = await self.next.exec(request)
        return response