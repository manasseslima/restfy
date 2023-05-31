from restfy import Application, Request
from .api.views import router as root


app = Application(
    title='Test Application',
    description='Used by test'
)
app.register_router('/', router=root)
