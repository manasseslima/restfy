import pytest
from restfy import Application, Client, CORSConfig, Request

# --- apps ---

app_wildcard = Application()
client_wildcard = Client(app_wildcard)

app_specific = Application()
app_specific.configure_cors(
    allow_origins=['https://example.com', 'https://app.example.com'],
    allow_methods=['GET', 'POST', 'PUT'],
    allow_headers=['Content-Type', 'Authorization'],
    max_age=3600,
)
client_specific = Client(app_specific)

app_creds = Application()
app_creds.configure_cors(
    allow_origins=['https://secure.example.com'],
    allow_credentials=True,
    expose_headers=['X-Custom-Header'],
)
client_creds = Client(app_creds)

app_ctor = Application(cors=CORSConfig(allow_origins=['https://ctor.example.com']))
client_ctor = Client(app_ctor)


@app_wildcard.get('/data')
@app_specific.get('/data')
@app_creds.get('/data')
@app_ctor.get('/data')
async def get_data():
    return {'ok': True}


# --- wildcard ---

@pytest.mark.asyncio
async def test_wildcard_any_origin():
    res = await client_wildcard.get('/data', headers={'Origin': 'https://any.com'})
    assert res.status == 200
    assert res.headers.get('Access-Control-Allow-Origin') == '*'


@pytest.mark.asyncio
async def test_wildcard_no_origin_header():
    res = await client_wildcard.get('/data')
    assert res.status == 200
    assert 'Access-Control-Allow-Origin' not in res.headers


# --- specific origins ---

@pytest.mark.asyncio
async def test_specific_origin_allowed():
    res = await client_specific.get('/data', headers={'Origin': 'https://example.com'})
    assert res.status == 200
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://example.com'
    assert res.headers.get('Vary') == 'Origin'


@pytest.mark.asyncio
async def test_specific_second_origin_allowed():
    res = await client_specific.get('/data', headers={'Origin': 'https://app.example.com'})
    assert res.status == 200
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://app.example.com'


@pytest.mark.asyncio
async def test_specific_origin_denied():
    res = await client_specific.get('/data', headers={'Origin': 'https://evil.com'})
    assert res.status == 200
    assert 'Access-Control-Allow-Origin' not in res.headers


# --- preflight ---

@pytest.mark.asyncio
async def test_preflight_allowed_origin():
    res = await client_specific.options(
        '/data',
        headers={
            'Origin': 'https://example.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type',
        },
    )
    assert res.status == 204
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://example.com'
    assert 'POST' in res.headers.get('Access-Control-Allow-Methods', '')
    assert 'Content-Type' in res.headers.get('Access-Control-Allow-Headers', '')
    assert res.headers.get('Access-Control-Max-Age') == '3600'


@pytest.mark.asyncio
async def test_preflight_denied_origin():
    res = await client_specific.options(
        '/data',
        headers={
            'Origin': 'https://evil.com',
            'Access-Control-Request-Method': 'POST',
        },
    )
    assert res.status == 204
    assert 'Access-Control-Allow-Origin' not in res.headers


# --- credentials ---

@pytest.mark.asyncio
async def test_credentials_specific_origin():
    res = await client_creds.get('/data', headers={'Origin': 'https://secure.example.com'})
    assert res.status == 200
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://secure.example.com'
    assert res.headers.get('Access-Control-Allow-Credentials') == 'true'
    assert res.headers.get('Access-Control-Expose-Headers') == 'X-Custom-Header'
    assert res.headers.get('Vary') == 'Origin'


@pytest.mark.asyncio
async def test_credentials_wrong_origin_denied():
    res = await client_creds.get('/data', headers={'Origin': 'https://other.com'})
    assert res.status == 200
    assert 'Access-Control-Allow-Origin' not in res.headers
    assert 'Access-Control-Allow-Credentials' not in res.headers


# --- CORSConfig passed to constructor ---

@pytest.mark.asyncio
async def test_cors_config_via_constructor():
    res = await client_ctor.get('/data', headers={'Origin': 'https://ctor.example.com'})
    assert res.status == 200
    assert res.headers.get('Access-Control-Allow-Origin') == 'https://ctor.example.com'
