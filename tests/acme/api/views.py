from restfy import Router, Request
from .servers.views import router as servers

router = Router()
router.register_router('/servers', servers)


@router.get('/health')
async def health_handler(
        request: Request
):
    res = {
        'name': request.app.title
    }
    return res
