import pytest
from restfy import Application, Client, Request
from .acme.main import app


client = Client(app)


@pytest.mark.asyncio
async def teste_client_application():
    res = await client.get('/')
    assert res.status == 200
    assert res.content == b'root'
    assert res.data == 'root'
    assert res.headers['Content-Type'] == 'text/plain'


@pytest.mark.asyncio
async def teste_json_response():
    res = await client.get('/servers')
    assert res.status == 200
    assert res.content == b'[{"id": 1, "name": "Hotbike"}, {"id": 2, "name": "SimpleSky"}]'
    data = res.parser()
    assert data[0]['id'] == 1
    assert res.headers['Content-Type'] == 'application/json'


@pytest.mark.asyncio
async def teste_request_query_args():
    res = await client.get('/servers/1')
    assert res.status == 200
    data = res.parser()
    assert data['name'] == 'Hotbike'
