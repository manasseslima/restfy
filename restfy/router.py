

class Route:
    def __init__(self, handler):
        self.handler = handler

    async def exec(self, request):
        return await self.handler(request)


class Router:
    def __init__(self):
        self.routers = {}

    def add_route(self, path, handle, method='GET'):
        if path in self.routers:
            self.routers[path][method.upper()] = Route(handle)
        else:
            self.routers[path] = {
                method.upper(): Route(handle)
            }

    async def get(self, request):
        properties = {'request': request}
        res = await self.routers[request.url][request.method](**properties)
        return res

    def match(self, url, method):
        route = None
        if url in self.routers and self.routers[url][method]:
            return self.routers[url][method]
        return None

