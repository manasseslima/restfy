# restfy
A small rest framework.


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

### Receiving JSON data and args from request object

```python
...
from restfy.http import Response, Request
...
async def handler(request: Request) -> Response:
    ...
    args = request.args()  # A dict with querystring values.
    data = request.dict()  # Try deserialise body in a dict.
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

### Returning a resonse with custom informations

```python
from restfy.http import Response, Request

...

async def handler(request: Request, pk: int) -> Response:
    data = f'restfy: pk {pk}'
    headers = {
        'Content-Type': 'application/json'
    }
    return Response(data, status=400, headers=headers)

...
```

