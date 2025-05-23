import os.path

from restfy import Application, Server
from tests.acme.api.views import router as root
from tests.acme.middlewares import SomeMiddleware, AnotherMiddleware


app = Application(
    title='ACME API',
    description='Used by test'
)
app.register_router('/', router=root)
app.register_middleware(SomeMiddleware)
app.register_middleware(AnotherMiddleware)


if __name__ == '__main__':
    ssl_key = os.path.expanduser('~/chave_privada.pem')
    ssl_crt = os.path.expanduser('~/certificado.pem')
    server = Server(app=app, ssl_key=ssl_key, ssl_crt=ssl_crt)
    server.run()
