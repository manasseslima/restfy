from restfy import Router, Request
from .base import database
from .models import ServerModel


router = Router()


@router.get('')
async def root_handler():
    return "root"


@router.get('/servers')
async def get_servers_list():
    servers = list(database['server'].values())
    return servers


@router.get('/servers/{key}')
async def get_servers_detail(
        request: Request,
        key: int
):
    args = request.path_args,
    server = database['server'].get(key, {})
    return server


@router.post('/servers')
async def insert_new_server(
        payload: ServerModel
):
    key = payload.id
    database['server'][key] = payload.dict()
    return {}


@router.put('/servers/{key}')
async def update_server_item(
        request: Request,
        payload: ServerModel,
        mode: str,
):
    key = int(request.vars['key'])
    data = database['server'][key]
    data.update(payload.dict())
    return data

