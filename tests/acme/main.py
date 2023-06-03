from restfy import Application, Server
from tests.acme.api.views import router as root


app = Application(
    title='Test Application',
    description='Used by test'
)
app.register_router('/', router=root)


if __name__ == '__main__':
    server = Server(app=app)
    server.run()
