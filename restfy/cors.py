class CORSConfig:
    def __init__(
        self,
        *,
        allow_origins: list[str] | str = '*',
        allow_methods: list[str] = None,
        allow_headers: list[str] = None,
        allow_credentials: bool = False,
        max_age: int = 0,
        expose_headers: list[str] = None,
    ):
        if isinstance(allow_origins, str):
            allow_origins = [allow_origins]
        self.allow_origins: list[str] = allow_origins
        self.allow_methods: list[str] = allow_methods or []
        self.allow_headers: list[str] = allow_headers or []
        self.allow_credentials: bool = allow_credentials
        self.max_age: int = max_age
        self.expose_headers: list[str] = expose_headers or []

    def is_origin_allowed(self, origin: str) -> bool:
        return '*' in self.allow_origins or origin in self.allow_origins

    def get_response_headers(self, request_origin: str = '') -> dict:
        if not request_origin or not self.is_origin_allowed(request_origin):
            return {}
        if '*' in self.allow_origins and not self.allow_credentials:
            origin_value = '*'
        else:
            origin_value = request_origin
        headers = {'Access-Control-Allow-Origin': origin_value}
        if origin_value != '*':
            headers['Vary'] = 'Origin'
        if self.allow_credentials:
            headers['Access-Control-Allow-Credentials'] = 'true'
        if self.allow_methods:
            headers['Access-Control-Allow-Methods'] = ', '.join(self.allow_methods)
        if self.allow_headers:
            headers['Access-Control-Allow-Headers'] = ', '.join(self.allow_headers)
        if self.max_age:
            headers['Access-Control-Max-Age'] = str(self.max_age)
        if self.expose_headers:
            headers['Access-Control-Expose-Headers'] = ', '.join(self.expose_headers)
        return headers
