# restfy
A small rest framework.

[![Stable Version](https://img.shields.io/pypi/v/restfy?label=pypi)](https://pypi.org/project/restfy/)


## Instalation

```shell
pip install restfy
```

## Usage

### Minimal usage

```python
from restfy import Application, Server
from restfy.http import Response, Request


async def handler(request: Request) -> Response:
    data = 'restfy'
    return Response(data)


app = Application()
app.add_route('/', handler, method='GET')

server = Server(app)
server.run()

```

### Adding route by router decorator
A route can be added by decorating handler function with .get, .post, .put, .delete or .path methods.
```python
from restfy import Application, Router, Request, Response

# By using router object
router = Router()

@router.get('')
async def handler(request: Request) -> Response:
    ret = {}
    return Response(ret)


app = Application()
app.register_router('', router=router)

# Or by app router decorator
@app.post('')
async def other_handler(request: Request) -> Response:
    ret = request.data
    return Response(ret)

...


```

### Receiving JSON data and args from request object
By default, Restfy will try to deserialize body data into request object data property by content type header information.
You can prefer deserialize body value manually or using dict request method. 
For this case, it's recommended to disable the process of deserialize by parsing False to prepare_request_data in Application.

The querystring values are deserialized using args() request method. The raw querystring is on query request attribute.

```python
...

from restfy.http import Response, Request

...

async def handler(request: Request) -> Response:
    data = request.data  # pre-deserialized body data before execute handler.
    args = request.args()  # A dict with querystring values.
    data = request.dict()  # Try deserialize body data in a dictionary. Recommended to use request.data instead.
    query = request.query
    ...

```

### Parsing value in url path.

If a path item is inside {}, its a variable. The handler function should have a parameter with the same name.

```python
from restfy import Application, Server
from restfy.http import Response, Request


async def handler(request: Request, pk: int) -> Response:
    data = f'restfy: pk {pk}'
    return Response(data)


app = Application()
app.add_route('/{pk}', handler, method='GET')

...
```

### Returning a response with custom 
By default, the Response class set 200 as status code. 
The content type is identified dynamically by data type. 
These parameters may be changed instancing the response passing status, headers and content_type parameters.

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



### Middlewares
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


