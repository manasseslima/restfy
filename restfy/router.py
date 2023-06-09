from restfy.request import Request
from restfy.handler import Handler


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
        handler = Handler(handle)
        node = path.pop(0)
        if websocket:
            method = 'GET'
        if node.startswith('{'):
            name = node[1:-1]
            if self.variable:
                handler.variable_name = name
                route = self.variable
            else:
                route = Route(websocket=websocket)
                route.is_variable = True
                route.name = name
                self.variable = route
        else:
            route = self.routes.get(node, Route(websocket=websocket))
            route.name = node
            self.routes[node] = route
        if path:
            route.add_node(path=path, handle=handle, method=method, websocket=websocket)
        else:
            # handlers = route.handlers if route.is_variable else self.handlers
            route.handlers[method] = handler
            # handlers[method] = handler
            ...

    def add_handler(self, func, method: str):
        handler = Handler(func)
        self.handlers[method] = handler

    async def exec(self, request: Request):
        handler = self.handlers[request.method]
        if self.prepare_data and request.app.prepare_request_data:
            request.prepare_data()
        for key, value in self.properties.items():
            request.path_args[key] = value
            request.vars[key] = value
        return await handler.execute(request)


class Router(Route):
    def __init__(self, base_url=''):
        super().__init__()
        self.base_url = base_url

    def add_route(
            self,
            path: str,
            handle: callable,
            *,
            method: str = 'GET',
            websocket: bool = False
    ):
        path = path[1:].split('/')
        if len(path) == 1 and path[0] == '':
            self.add_handler(handle, method)
        else:
            self.add_node(path=path, handle=handle, method=method, websocket=websocket)

    def register_router(self, path, router):
        nodes = path[1:].split('/')
        if len(nodes) == 1 and nodes[0] == '':
            self.handlers = router.handlers
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
                elif node.startswith('{'):
                    if self.variable:
                        route = self.variable
                    else:
                        route = Route()
                        route.is_variable = True
                        route.name = node[1:-1]
                        self.variable = route
                        routes = route.routes
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
        args = {}
        route = None
        while len(nodes) > 0:
            node = nodes.pop(0)
            route = routes.get(node, None)
            if not route:
                if variable:
                    route = variable
                    args[route.name] = node
                else:
                    break
            routes = route.routes
            variable = route.variable
        if route:
            if method in route.handlers:
                route.properties = args
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
