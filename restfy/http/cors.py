

class AccessControl:
    allow_origin = '*'
    expose_headers = []
    max_age = 0.0
    allow_credentials = False
    allow_methods = []
    allow_headers = []

    def get_response_headers(self):
        headers = {
            'Access-Control-Allow-Origin': self.allow_origin,
        }
        if self.allow_methods:
            headers['Access-Control-Allow-Methods'] = ','.join(self.allow_methods)
        if self.allow_headers:
            headers['Access-Control-Allow-Headers'] = ','.join(self.allow_headers)
        if self.allow_credentials:
            headers['Access-Control-Allow-Credentials'] = self.allow_credentials
        if self.max_age:
            headers['Access-Control-Max-Age'] = self.max_age
        if self.expose_headers:
            headers['Access-Control-Expose-Headers'] = self.expose_headers
        return headers


