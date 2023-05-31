import bike
from .request import Request
from .response import Response


class Handler:
    def __init__(self, func: callable):
        self.func: callable = func
        self.func_name: str = func.__name__
        self.parameters: dict = {}
        self.request_parameter: str = ''
        self.payload_parameter: str = ''
        self.payload_model = None
        self.return_type: type | None = None
        params = func.__annotations__
        for name, param in params.items():
            if issubclass(param, Request):
                self.request_parameter = name
            elif issubclass(param, bike.Model):
                self.payload_parameter = name
                self.payload_model = param
            elif name == 'return':
                self.return_type = param
            else:
                self.parameters[name] = param

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
        if self.request_parameter:
            args[self.request_parameter] = request
        if self.payload_parameter:
            instance = self.payload_model(**request.body)
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
