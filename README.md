# restfy
A small rest framework


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

### Receiving Json data and args from request object

```python
...
async def handler(request: Request) -> Response:
    ...
    args = request.args()  # A dict from querystring values.
    data = request.dict()  # Try deserialise body in a dict.
    ...

```
