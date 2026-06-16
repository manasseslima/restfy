import pytest
from restfy import Application, Client, Request

app = Application()
client = Client(app)


@app.get('/echo')
async def echo(request: Request):
    return dict(request.query_args)


@pytest.mark.asyncio
async def test_percent_encoded_space():
    res = await client.get('/echo?name=hello%20world')
    assert res.parser()['name'] == 'hello world'


@pytest.mark.asyncio
async def test_plus_as_space():
    res = await client.get('/echo?name=hello+world')
    assert res.parser()['name'] == 'hello world'


@pytest.mark.asyncio
async def test_encoded_plus_sign():
    res = await client.get('/echo?token=abc%2Bdef')
    assert res.parser()['token'] == 'abc+def'


@pytest.mark.asyncio
async def test_encoded_equals_in_value():
    res = await client.get('/echo?token=abc%3Ddef')
    assert res.parser()['token'] == 'abc=def'


@pytest.mark.asyncio
async def test_blank_value():
    res = await client.get('/echo?flag=')
    assert res.parser()['flag'] == ''


@pytest.mark.asyncio
async def test_multiple_params():
    res = await client.get('/echo?city=S%C3%A3o%20Paulo&country=BR')
    data = res.parser()
    assert data['city'] == 'São Paulo'
    assert data['country'] == 'BR'
