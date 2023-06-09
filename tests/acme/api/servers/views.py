from restfy import Router, Request
from tests.acme.base import database
from .nodes.views import router as nodes
from .models import ServerModel


router = Router()
router.register_router('/{key}/nodes', nodes)


@router.get('')
async def get_servers_list():
    servers = list(database['server'].values())
    return servers


@router.post('')
async def insert_new_server(
        payload: ServerModel
):
    key = payload.id
    data = payload.dict()
    database['server'][key] = data
    return data


@router.get('/{key}')
async def get_servers_detail(
        request: Request,
        key: int
):
    server = database['server'].get(key, {})
    return server


@router.put('/{key}')
async def update_server_item(
        request: Request,
        payload: ServerModel,
        mode: str,
):
    key = int(request.vars['key'])
    data = database['server'][key]
    data.update(payload.dict())
    return data


@router.delete('/{key}')
async def remove_server_item(
        request: Request,
        key: int
):
    res = database['server'][key]
    return res
