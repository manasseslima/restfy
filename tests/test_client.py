import pytest
from restfy import Application, Client, Request
from .acme.main import app


@pytest.mark.asyncio
async def teste_client_application():
    client = Client(app)
    res = await client.get('/')
    assert res.status == 200
    assert res.content == b'root'
    assert res.data == 'root'
    assert res.headers['Content-Type'] == 'text/plain'


@pytest.mark.asyncio
async def teste_request_arguments():
    client = Client(app)
    res = await client.get('/servers')
    assert res.status == 200
    assert res.content == b'[{"id": 1, "name": "Hotbike"}, {"id": 2, "name": "SimpleSky"}]'
    data = res.parser()
    assert data[0]['id'] == 1
    assert res.headers['Content-Type'] == 'application/json'
