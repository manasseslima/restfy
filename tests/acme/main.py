from restfy import Application, Request
from .base import database


app = Application(
    title='Test Application',
    description='Used by test'
)


@app.get('/')
async def root_handler():
    return "root"


@app.get('/servers')
async def get_servers_list():
    servers = list(database['server'].values())
    return servers


@app.get('/servers/{key}')
async def get_servers_list(
        request: Request
):
    args = request.args()
    key = args.get('key')
    server = database['server'].get(key, {})
    return server
