from httplus import Client
from restfy.request import Request
from restfy.response import Response

__all__ = [
    Request, Response, 'request', 'get', 'post', 'put', 'delete', 'patch'
]


async def request(
        method: str,
        url: str,
        data: ... = None,
        headers: dict = None
):
    client = Client()
    res = await client.request(
        method=method,
        url=url,
        data=data,
        headers=headers
    )
    return res


async def get(
        url: str,
        *,
        headers: str = None
):
    res = await request(method='GET', url=url, headers=headers)
    return res


async def post(
        url: str,
        data: ...,
        *,
        headers: dict = None
):
    res = await request(method='POST', url=url, data=data, headers=headers)
    return res


async def put(
        url: str,
        data: ...,
        *,
        headers: dict = None
):
    res = await request(method='PUT', url=url, data=data, headers=headers)
    return res


async def delete(
        url: str,
        *,
        headers: dict = None
):
    res = await request(method='DELETE', url=url, headers=headers)
    return res


async def patch(
        url: str,
        data: ...,
        *,
        headers: dict = None
):
    res = await request(method='PATCH', url=url, data=data, headers=headers)
    return res
