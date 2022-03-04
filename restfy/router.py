import inspect
from restfy.http import Request


class Handler:
    def __init__(self, func):
        self.func = func
        args = inspect.getfullargspec(func).annotations
        self.return_type = args.pop('return')
        self.parameters = args

    async def execute(self, properties):
        args = {}
        for key, kind in self.parameters.items():
            value = properties.get(key)
            if not value:
                raise Exception(f'Parameter {key}')
            if kind in [int, float, bool]:
                try:
                    value = kind(value)
                except Exception as e:
                    raise Exception(f'Error try cast value "{value}" {key} {kind}: {e}')
            args[key] = value
        ret = await self.func(**args)
        return ret


class Route:
    def __init__(self, name='', node='', path=None, handle=None, method='', prepare_data=True):
        self.properties = {}
        self.handlers = {}
        self.routes = {}
        self.variable = None
        self.is_variable = False
        self.variable_type = str
        self.name = name
        self.prepare_data: bool = prepare_data

    def add_node(self, path, handle, method='GET'):
        node = path.pop(0)
        if node.startswith('{'):
            if self.variable:
                route = self.variable
            else:
                route = Route()
                route.is_variable = True
                route.name = node[1:-1]
                self.variable = route
        else:
            route = self.routes.get(node, Route())
            route.name = node
            self.routes[node] = route
        if path:
            route.add_node(path=path, handle=handle, method=method)
        else:
            route.add_handler(Handler(handle), method)

    def add_handler(self, handle, method):
        self.handlers[method] = handle

    async def exec(self, request: Request):
        handler = self.handlers[request.method]
        if self.prepare_data and request.app.prepare_request_data:
            request.prepare_data()
        properties = {'request': request, **self.properties}
        return await handler.execute(properties)


class Router(Route):
    def __init__(self, base_url=''):
        super().__init__()
        self.base_url = base_url

    def add_route(self, path, handle, method='GET'):
        path = path[1:].split('/')
        if len(path) == 1 and path[0] == '':
            self.add_handler(Handler(handle), method)
        else:
            self.add_node(path=path, handle=handle, method=method)

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
                    if routes[node].routes:
                        routes = routes[node].routes
                    else:
                        routes = routes[node].variable

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
