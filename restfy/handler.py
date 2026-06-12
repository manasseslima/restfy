import inspect
import bike
from .request import Request
from .response import Response
from .websocket import WebSocket


class Handler:
    def __init__(self, func: callable):
        self.func: callable = func
        self.func_name: str = func.__name__
        self.variable_name: str = ''
        self.parameters: dict = {}
        self.request_parameter: str = ''
        self.payload_parameter: str = ''
        self.websocket_parameter: str = ''
        self.payload_model = None
        self.return_type: type | None = None
        params = func.__annotations__
        for name, param in params.items():
            if name == 'return':
                self.return_type = param
            elif not inspect.isclass(param):
                self.parameters[name] = param
            elif issubclass(param, WebSocket):
                self.websocket_parameter = name
            elif issubclass(param, Request):
                self.request_parameter = name
            elif issubclass(param, bike.Model):
                self.payload_parameter = name
                self.payload_model = param
            else:
                self.parameters[name] = param

    async def execute(self, request: Request):
        args = {}
        for key, kind in self.parameters.items():
            value = request.vars.pop(key, None)
            if value is None:
                value = request.params.pop(key, None)
            if value is None:
                continue
            if kind in [int, float, bool]:
                try:
                    value = kind(value)
                except Exception as e:
                    raise Exception(f'Error try cast value "{value}" {key} {kind}: {e}')
            args[key] = value
        if self.request_parameter:
            args[self.request_parameter] = request
        if self.payload_parameter:
            instance = self.payload_model(**request.data)
            args[self.payload_parameter] = instance
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

    async def execute_websocket(self, websocket: WebSocket, request: Request):
        args = {}
        for key, kind in self.parameters.items():
            value = request.vars.pop(key, None)
            if value is None:
                value = request.params.pop(key, None)
            if value is None:
                continue
            if kind in [int, float, bool]:
                try:
                    value = kind(value)
                except Exception as e:
                    raise Exception(f'Error try cast value "{value}" {key} {kind}: {e}')
            args[key] = value
        if self.request_parameter:
            args[self.request_parameter] = request
        if self.websocket_parameter:
            args[self.websocket_parameter] = websocket
        await self.func(**args)
