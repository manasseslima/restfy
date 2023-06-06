from restfy import Router, Request
from tests.acme.base import database


router = Router()


@router.get('')
async def get_nodes_list(
        request: Request
):
    return []

