# restfy
A small rest framework


## Instalation

```shell
pip install restfy
```

## Basic usage

```python
import asyncio
from restfy import Application
from restfy.http import Response, Request


async def root(request: Request) -> Response:
    data = 'restfy'
    return Response(data)


app = Application()
app.add_route('/', root, method='GET')

asyncio.run(app.run())

```
