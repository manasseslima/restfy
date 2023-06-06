from .request import Request
from .response import Response


class Middleware:
    def __init__(self):
        self.next = None

    async def exec(self, request: Request) -> Response:
        response = await self.forward(request)
        return response

    async def forward(self, request: Request) -> Response:
        response = await self.next.exec(request)
        return response
