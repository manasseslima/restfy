import pytest
from restfy import Application, Client, Request, Response

app = Application()
client = Client(app)


@app.get('/read-cookie')
async def read_cookie(request: Request):
    session = request.cookies.get('session', '')
    return {'session': session}


@app.get('/read-multi-cookie')
async def read_multi_cookie(request: Request):
    return {k: v for k, v in request.cookies.items()}


@app.get('/set-cookie')
async def set_cookie_handler():
    res = Response({'ok': True})
    res.set_cookie('session', 'abc123')
    return res


@app.get('/set-cookie-options')
async def set_cookie_options_handler():
    res = Response({'ok': True})
    res.set_cookie(
        'token', 'secret',
        path='/api',
        domain='example.com',
        max_age=3600,
        httponly=True,
        secure=True,
        samesite='strict',
    )
    return res


@app.get('/set-multi-cookie')
async def set_multi_cookie_handler():
    res = Response({'ok': True})
    res.set_cookie('a', '1')
    res.set_cookie('b', '2', httponly=True)
    return res


@app.get('/delete-cookie')
async def delete_cookie_handler():
    res = Response({'ok': True})
    res.delete_cookie('session')
    return res


@app.get('/no-cookie')
async def no_cookie_handler(request: Request):
    return {'has_cookies': bool(request.cookies)}


# --- request-side tests ---

@pytest.mark.asyncio
async def test_read_single_cookie():
    res = await client.get('/read-cookie', headers={'Cookie': 'session=abc123'})
    assert res.status == 200
    assert res.parser() == {'session': 'abc123'}


@pytest.mark.asyncio
async def test_read_multiple_cookies():
    res = await client.get('/read-multi-cookie', headers={'Cookie': 'a=1; b=2; c=3'})
    assert res.status == 200
    data = res.parser()
    assert data == {'a': '1', 'b': '2', 'c': '3'}


@pytest.mark.asyncio
async def test_no_cookie_header_yields_empty_dict():
    res = await client.get('/no-cookie')
    assert res.status == 200
    assert res.parser() == {'has_cookies': False}


@pytest.mark.asyncio
async def test_cookie_with_equals_in_value():
    """Cookie values that contain '=' (e.g. base64) must be preserved."""
    res = await client.get('/read-cookie', headers={'Cookie': 'session=abc=xyz=='})
    assert res.status == 200
    assert res.parser() == {'session': 'abc=xyz=='}


# --- response-side tests ---

@pytest.mark.asyncio
async def test_set_cookie_added_to_cookies_list():
    res = await client.get('/set-cookie')
    assert res.status == 200
    assert len(res.cookies) == 1
    assert res.cookies[0].startswith('session=abc123')


@pytest.mark.asyncio
async def test_set_cookie_default_path():
    res = await client.get('/set-cookie')
    assert 'Path=/' in res.cookies[0]


@pytest.mark.asyncio
async def test_set_cookie_with_options():
    res = await client.get('/set-cookie-options')
    assert res.status == 200
    assert len(res.cookies) == 1
    cookie = res.cookies[0]
    assert 'token=secret' in cookie
    assert 'Path=/api' in cookie
    assert 'Domain=example.com' in cookie
    assert 'Max-Age=3600' in cookie
    assert 'HttpOnly' in cookie
    assert 'Secure' in cookie
    assert 'SameSite=Strict' in cookie


@pytest.mark.asyncio
async def test_multiple_set_cookie():
    res = await client.get('/set-multi-cookie')
    assert res.status == 200
    assert len(res.cookies) == 2


@pytest.mark.asyncio
async def test_multiple_set_cookie_in_rendered_bytes():
    res = await client.get('/set-multi-cookie')
    rendered = res.render()
    assert rendered.count(b'Set-Cookie:') == 2


@pytest.mark.asyncio
async def test_delete_cookie_sets_max_age_zero():
    res = await client.get('/delete-cookie')
    assert res.status == 200
    assert len(res.cookies) == 1
    cookie = res.cookies[0]
    assert 'session=' in cookie
    assert 'Max-Age=0' in cookie
    assert '1970' in cookie


@pytest.mark.asyncio
async def test_set_cookie_appears_in_rendered_response():
    res = await client.get('/set-cookie')
    rendered = res.render()
    assert b'Set-Cookie:session=abc123' in rendered


@pytest.mark.asyncio
async def test_no_set_cookie_when_none_added():
    app2 = Application()
    client2 = Client(app2)

    @app2.get('/plain')
    async def plain():
        return {'ok': True}

    res = await client2.get('/plain')
    rendered = res.render()
    assert b'Set-Cookie' not in rendered
