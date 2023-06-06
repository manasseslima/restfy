# restfy
A small rest framework.

[![Stable Version](https://img.shields.io/pypi/v/restfy?label=pypi)](https://pypi.org/project/restfy/)


## Instalation

```shell
pip install restfy
```

## Usage

### Minimal usage
A basic Restfy application is showed below.

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
This code fragment sets up a basic web application using your asynchronous web application framework. 
It defines a route for a POST request at the root URL and returns a response with the request data. 
The server is then started to handle incoming requests.

In this code, the **restfy** module is imported, and the necessary classes **Application**, **Server**, **Request**, and **Response** are imported from it.

An instance of the Application class is created and assigned to the variable app. This class represents the restfy application framework itself.

The `@app.post('/')` decorator is used to define a route for the HTTP POST method at the root URL ("/") of the application. When a POST request is made to this URL, the handler function will be called.

The handler function is an asynchronous function that takes a request parameter of type Request. It creates a Response object with a data and returns it.

An instance of the Server class is created, passing the app object as a parameter to associate the server with the application.

Finally, the run() method is called on the server object, which starts the server and makes it listen for incoming requests.

The routes also can be added by using `.add_route(path, handler, method)` application method.

```python
from restfy import Application, Server, Response, Request


async def handler(request: Request) -> Response:
    data = f'{request.method}: {request.url}'
    return Response(data)


app = Application()
app.add_route('/', handler, method='GET')
...
```

### Adding route by router decorator

For applications with a great number of routes is necessary a better modules organization.
To help in this process, Restfy has a class to manager the routes, **Router** class.

The Router class is similar to Application class to register routes.
Then, a cluster of routes can be created as necessary.
```python
# servers.py
from restfy import Router

router = Router()


@router.get('')
async def get_servers_list():
    ret = []
    return ret


@router.post('')
async def create_new_server():
    ...
    return {}

...

# application.py
from restfy import Application
from .servers import router as servers


app = Application()
app.register_router('/servers', servers)
...
```
As we can see, the routes are defined on other file by a **Route** instance.
The app object registry this through `.register_router(path, router)`.

With this approach, several routes can be registered with different routes.


## Receiving data and args from request object

The information can be passed by path variables, query_string parameters, request body and request headers.

Below, is showed a condensed example how to that information are distributed inside **Request** object.

```python
...
@router.put('/servers/{key}')
async def handler(
        request: Request,
        key: int
) -> Response:
    headers: dict = request.headers  # request headers 
    ...
    # Body HTTP request
    body: bytes = request.body  # The raw binary request body. 
    dada: dict | list | None = request.data  # A deserialized body.
    ...
    # The path variables
    args: dict = request.path_args  # Complete variables 
    vars: dict = request.vars  # Variables not explicit used by function
    ...
    # The query_string parameters
    query: dict = request.query_args  # Complete 
    params: dict = request.params  # Incomplete
    ...
    return Response([])
...
```
If you need a more explict variable declaration, you can declare it as a function parameter.
Restfy will identify this value on Request path_args or query_args and set it.
The query_args and path_args will not be affected by the Request params and vars will be.
That attributes hold the values are not used as function parameter.
Then, in the fragment above, the path_args will have the key value and the vars will be empty because key value is setted as a funcion parameter.

The Request try parse the body bytes to data based on its content type.
For example, if the request content type is a `application/json`, the data will set by json format.


## Returning data

If we are creating a server, it a fact we want return some data.
It can be done by a Response instance object passing data attribute and optionality, the status and headers.
In addition, we can just return a value that Restfy will try to create a Response object instance based on value type.

The return also can be a tuple with value and the status code.

That shortcuts are very useful for most common situations by when the data are a file body, we need create a Response instance with the correct content type.

In the future Restfy release, probably will bring exclusive Response objects but will not cover all cases. 



```python
from restfy.http import Response, Request

...

async def handler(request: Request, pk: int) -> Response:
    data = f'<b>restfy: pk {pk}</b>'
    headers = {
        'Content-Type': 'text/html'
    }
    return Response(data, status=400, headers=headers)

...

async def handler_other(request: Request, pk: int) -> Response:
    data = f'<b>restfy: pk {pk}</b>'
    return Response(data, status=400, content_type='text/html')

...
```



## Middlewares

Restfy uses middleware creating a class with .exec() method. 
The parameter request must be passed into exec method.

The Application has the method .register_middleware() to register middlewares. 
The register order is the same order of execution.

```python
from restfy import Application, Middleware


class DefaultMiddleware(Middleware):
    async def exec(self, request):
        # Do something with request object
        ...
        response = await self.forward(request)
        ...
        # Do something with response object
        return response


app = Application()
app.register_middleware(DefaultMiddleware)

```

## HTTP client requests

With http module, you can do asynchronous requests to other services.
The most simple request can be seen below.

```python
from restfy import http
...
res = await http.get('https://someserver.api/endpoint')
print(res.status)
# 200
```
In addition to the get function, others functions are available like 
post(), put(), delete() and patch(). 
If other request method are necessary, we can use request() function passing method param.
The next example shows a more complex example.
```python
from restfy import http


data = {
    'name': 'Nick',
    'surname': 'Lauda'
}
headers = {
    'Content-Type': 'application/json'
}
url = 'https://someserver.api/endpoint'
res = await http.post(url=url, data=data, headers=headers)
print(res.status)
# 200
```