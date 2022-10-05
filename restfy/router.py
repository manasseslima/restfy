import inspect
from restfy.http import Request, Response


class Handler:
    def __init__(self, func):
        self.func = func
        args = inspect.getfullargspec(func).annotations
        if 'return' in args:
            self.return_type = args.pop('return')
        self.parameters = args

    async def execute(self, properties, request):
        args = {}
        for key, kind in self.parameters.items():
            value = properties.get(key)
            if not value:
                value = request.args.pop(key, '')
            if not value:
                continue
            if kind in [int, float, bool]:
                try:
                    value = kind(value)
                except Exception as e:
                    raise Exception(f'Error try cast value "{value}" {key} {kind}: {e}')
            args[key] = value
        try:
            ret = await self.func(**args)
            if isinstance(ret, tuple):
                ret = Response(ret[0], ret[1])
            elif isinstance(ret, (dict, list, str, int, float, bool)):
                ret = Response(ret)
        except Exception as e:
            data = {
                'message': 'Error on executing request',
                'detail': str(e)
            }
            ret = Response(data, status=400)
        return ret


class Route:
    def __init__(self, name='', node='', path=None, handle=None, method='', prepare_data=True, websocket=False):
        self.properties = {}
        self.handlers = {}
        self.routes = {}
        self.variable = None
        self.is_variable = False
        self.variable_type = str
        self.name = name
        self.prepare_data: bool = prepare_data
        self.is_websocket = websocket

    def __repr__(self):
        return f'{self.__class__}: {self.name}'

    def add_node(self, path, handle, method='GET', websocket=False):
        node = path.pop(0)
        if websocket:
            method = 'GET'
        if node.startswith('{'):
            if self.variable:
                route = self.variable
            else:
                route = Route(websocket=websocket)
                route.is_variable = True
                route.name = node[1:-1]
                self.variable = route
        else:
            route = self.routes.get(node, Route(websocket=websocket))
            route.name = node
            self.routes[node] = route
        if path:
            route.add_node(path=path, handle=handle, method=method, websocket=websocket)
        else:
            route.add_handler(Handler(handle), method)

    def add_handler(self, handle, method):
        self.handlers[method] = handle

    async def exec(self, request: Request):
        handler = self.handlers[request.method]
        if self.prepare_data and request.app.prepare_request_data:
            request.prepare_data()
        properties = {'request': request, **self.properties}
        return await handler.execute(properties, request)


class Router(Route):
    def __init__(self, base_url=''):
        super().__init__()
        self.base_url = base_url

    def add_route(self, path, handle, method='GET', websocket=False):
        path = path[1:].split('/')
        if len(path) == 1 and path[0] == '':
            self.add_handler(Handler(handle), method)
        else:
            self.add_node(path=path, handle=handle, method=method, websocket=websocket)

    def register_router(self, path, router):
        nodes = path[1:].split('/')
        if len(nodes) == 1 and nodes[0] == '':
            self.routes = router.routes
            self.variable = router.variable
            self.is_variable = router.is_variable
        else:
            routes = self.routes
            while True:
                node = nodes.pop(0)
                if len(nodes) == 0:
                    routes[node] = router
                    break
                else:
                    if node in routes:
                        if routes[node].routes:
                            routes = routes[node].routes
                        else:
                            routes = routes[node].variable
                    else:
                        routes[node] = Router()
                        routes = routes[node].routes

    def match(self, url, method):
        nodes = url[1:].split('/')
        if len(nodes) == 1 and nodes[0] == '':
            return self
        routes = self.routes
        variable = self.variable
        properties = {}
        while len(nodes) > 0:
            node = nodes.pop(0)
            route = routes.get(node, None)
            if not route:
                if variable:
                    route = variable
                    properties[route.name] = node
                else:
                    break
            routes = route.routes
            variable = route.variable
        if route:
            if method in route.handlers:
                route.properties = properties
            else:
                route = None
        return route

    def get(self, path):
        def wrapper(func):
            self.add_route(path, handle=func)
            return func
        return wrapper

    def post(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='POST')
            return func
        return wrapper

    def put(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='PUT')
            return func
        return wrapper

    def delete(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='DELETE')
            return func
        return wrapper

    def patch(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='PATCH')
            return func
        return wrapper

    def options(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='OPTIONS')
            return func
        return wrapper

    def head(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='HEAD')
            return func
        return wrapper

    def websocket(self, path):
        def wrapper(func):
            self.add_route(path, handle=func, method='GET', websocket=True)
            return func
        return wrapper
