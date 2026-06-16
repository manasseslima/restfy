# Restfy
A lightweight async REST framework for Python 3.10+.

[![Stable Version](https://img.shields.io/pypi/v/restfy?label=pypi)](https://pypi.org/project/restfy/)


## Installation

```shell
pip install restfy
```

## Usage

### Minimal application

A basic Restfy application is shown below.

```python
from restfy import Application, Server, Request, Response

app = Application()


@app.post('/')
async def handler(request: Request) -> Response:
    ret = request.data
    return Response(ret)


server = Server(app)
server.run()
```

The `@app.post('/')` decorator registers a route for `POST /`. When a request
arrives, Restfy calls the handler, which receives a `Request` object and returns
a `Response`. `Server.run()` starts the asyncio event loop and begins accepting
connections.

Routes can also be registered programmatically via `app.add_route(path, handler, method)`:

```python
from restfy import Application, Server, Response, Request


async def handler(request: Request) -> Response:
    data = f'{request.method}: {request.url}'
    return Response(data)


app = Application()
app.add_route('/', handler, method='GET')
```

### Routers

For applications with a large number of routes, better module organization is
necessary. Restfy provides the **Router** class to group related routes together.

```python
# servers.py
from restfy import Router

router = Router()


@router.get('')
async def get_servers_list():
    return []


@router.post('')
async def create_new_server():
    return {}


# application.py
from restfy import Application
from .servers import router as servers_router

app = Application()
app.register_router('/servers', servers_router)
```

Routes are defined in a separate module using a `Router` instance. The
application mounts it under a base path with `register_router(path, router)`.
Multiple routers can be registered under different paths.

### Available HTTP method decorators

`get`, `post`, `put`, `delete`, `patch`, `options`, `head`, `websocket` are
available on both `Application` and `Router`.


## Receiving data from the request

Data can be passed via path variables, query string parameters, request body
and headers. The `Request` object exposes all of these:

```python
@router.put('/servers/{key}')
async def update_server(
        request: Request,
        key: int
) -> Response:
    headers: dict = request.headers        # request headers

    # Body
    body: bytes = request.body             # raw binary body
    data: dict | list | None = request.data  # deserialized body

    # Path variables
    path_args: dict = request.path_args    # all path variables
    vars: dict = request.vars              # path variables not bound to a parameter

    # Query string
    query_args: dict = request.query_args  # all query string parameters
    params: dict = request.params          # query parameters not bound to a parameter

    return Response([])
```

When a parameter is declared as a function argument (e.g. `key: int`), Restfy
extracts it automatically from `path_args` or `query_args` and performs type
conversion. `vars` and `params` hold only the values that were **not** consumed
as function parameters.

The request body is automatically deserialized into `request.data` based on the
`Content-Type` header:
- `application/json` → dict / list
- `application/x-www-form-urlencoded` → dict
- `multipart/form-data` → dict (fields) + `request.files` (uploaded files)


## Returning data

A handler can return:

- A `Response` instance for full control over status code, headers and body.
- A `dict`, `list`, `str`, `int`, `float` or `bool` — Restfy wraps it in a
  `Response` automatically.
- A `(data, status_code)` tuple.

```python
from restfy import Response, Request

# Full Response with custom headers
async def handler(request: Request, pk: int) -> Response:
    data = f'<b>restfy: pk {pk}</b>'
    return Response(data, status=200, headers={'Content-Type': 'text/html'})


# Using the content_type shortcut
async def handler_typed(request: Request, pk: int) -> Response:
    data = f'<b>restfy: pk {pk}</b>'
    return Response(data, status=200, content_type='text/html')


# Shorthand — Restfy infers the Response
async def handler_short(request: Request):
    return {'id': 1, 'name': 'restfy'}


# Tuple shorthand — (data, status_code)
async def handler_tuple(request: Request):
    return {'error': 'not found'}, 404
```

When returning binary data (e.g. a PDF), always use a `Response` instance with
the appropriate `content_type`.


## CORS

Cross-Origin Resource Sharing is configured via `Application.configure_cors()` or by passing a `CORSConfig` instance to the constructor.

```python
from restfy import Application, CORSConfig

app = Application()

# Keyword-argument style
app.configure_cors(
    allow_origins=['https://example.com', 'https://app.example.com'],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Content-Type', 'Authorization'],
    allow_credentials=False,
    max_age=3600,
    expose_headers=['X-Custom-Header'],
)

# Constructor style
app2 = Application(cors=CORSConfig(allow_origins='*'))
```

`allow_origins` can be a single string (`'*'` for wildcard) or a list of allowed origins.
When a specific origin list is configured, only matching origins receive CORS headers and
`Vary: Origin` is added automatically. When `allow_credentials=True`, the wildcard `'*'`
is never sent — the echoed request origin is used instead, as required by the CORS spec.

Preflight (`OPTIONS`) requests are handled automatically and return `204 No Content` with
the appropriate CORS headers.


## Middlewares

Middlewares intercept requests and responses. Create a class that extends
`Middleware` and implement the `exec` method. Call `await self.forward(request)`
to pass the request to the next middleware or the route handler.

```python
from restfy import Application, Middleware


class DefaultMiddleware(Middleware):
    async def exec(self, request):
        # Modify the request before it reaches the handler
        request.headers['X-Request-Id'] = 'abc123'

        response = await self.forward(request)

        # Modify the response before it is returned to the client
        response.headers['X-Processed'] = 'true'
        return response


app = Application()
app.register_middleware(DefaultMiddleware)
```

Middlewares are executed in the order they are registered.


## HTTPS / TLS

Pass the certificate and key paths to `Server` to enable TLS. Restfy will
advertise HTTP/2 via ALPN when TLS is active.

```python
from restfy import Application, Server

app = Application()

server = Server(app, ssl_crt='cert.pem', ssl_key='key.pem')
server.run()
```


## Testing

Restfy ships a `Client` helper that bypasses the TCP layer, making it easy to
write fast unit tests without starting a real server.

```python
import pytest
from restfy import Application, Client

app = Application()

@app.get('/ping')
async def ping():
    return {'status': 'ok'}

client = Client(app)

@pytest.mark.asyncio
async def test_ping():
    res = await client.get('/ping')
    assert res.status == 200
    assert res.parser() == {'status': 'ok'}
```


## HTTP client

The `http` module provides an async HTTP client for calling external services.

```python
from restfy import http

# Simple GET request
res = await http.get('https://api.example.com/items')
print(res.status)  # 200

# POST with JSON body and custom headers
data = {'name': 'Nick', 'surname': 'Lauda'}
headers = {'Authorization': 'Bearer token123'}
res = await http.post('https://api.example.com/items', data=data, headers=headers)
print(res.status)  # 201
```

Available functions: `get`, `post`, `put`, `delete`, `patch`. For any other
method use `http.request(method, url, ...)`.
