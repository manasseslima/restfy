import pytest
from restfy import Application, Client, Request
from .acme.main import app


client = Client(app)


@pytest.mark.asyncio
async def teste_client_application():
    res = await client.get('/health')
    assert res.status == 200
    assert res.headers['Content-Type'] == 'application/json'
    data = res.parser()
    assert data['name'] == 'ACME API'


@pytest.mark.asyncio
async def teste_json_response():
    res = await client.get('/servers')
    assert res.status == 200
    data = res.parser()
    server = data[0]
    assert server['id'] == 1
    assert server['name'] == 'hotbike'
    assert res.headers['Content-Type'] == 'application/json'


@pytest.mark.asyncio
async def teste_request_path_args():
    res = await client.get('/servers/1')
    assert res.status == 200
    data = res.parser()
    assert data['name'] == 'hotbike'


@pytest.mark.asyncio
async def test_post_payload_model():
    data = {
        'id': 3,
        'name': 'brainstorm'
    }
    res = await client.post('/servers', data=data)
    assert res.status == 200


@pytest.mark.asyncio
async def test_put_payload_model():
    data = {
        'id': 1,
        'name': 'mixin'
    }
    url = '/servers/1?offset=3&size=20&mode=influx'
    res = await client.put(url, data=data)
    assert res.status == 200


@pytest.mark.asyncio
async def test_subrouters_with_key():
    # url = '/servers/1/nodes'
    # res = await client.get(url)
    # assert res.status == 200
    assert True


@pytest.mark.asyncio
async def teste_middleware_interception():
    data = {
        'id': 9,
        'name': 'trix'
    }
    url = '/servers'
    res = await client.post(url, data=data)
    assert res.status == 200
    assert res.headers['Acme-Transaction-Id'] == '123456789'
    assert res.headers['Acme-Session-Id'] == '987654321'
