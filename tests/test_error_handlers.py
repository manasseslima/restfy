import pytest
from restfy import Application, Client, Request, Response

app = Application()
client = Client(app)


# --- routes ---

@app.get('/ok')
async def ok():
    return {'status': 'ok'}


@app.get('/raise-value')
async def raise_value():
    raise ValueError('bad input')


@app.get('/raise-runtime')
async def raise_runtime():
    raise RuntimeError('something broke')


@app.get('/raise-custom')
async def raise_custom():
    raise TypeError('type mismatch')


@app.get('/return-422')
async def return_422():
    return Response({'detail': 'unprocessable'}, status=422)


# --- error handlers ---

@app.on_error(404)
async def not_found(request: Request):
    return Response({'error': 'not found', 'path': request.url}, status=404)


@app.on_error(422)
async def unprocessable(request: Request):
    return Response({'error': 'unprocessable entity'}, status=422)


@app.on_exception(ValueError)
async def handle_value_error(request: Request, exc: Exception):
    return Response({'error': 'validation error', 'detail': str(exc)}, status=422)


@app.on_exception(RuntimeError)
async def handle_runtime(request: Request, exc: Exception):
    return Response({'error': 'runtime error', 'detail': str(exc)}, status=500)


# --- tests ---

@pytest.mark.asyncio
async def test_normal_request_unaffected():
    res = await client.get('/ok')
    assert res.status == 200
    assert res.parser() == {'status': 'ok'}


@pytest.mark.asyncio
async def test_on_error_404():
    res = await client.get('/does-not-exist')
    assert res.status == 404
    data = res.parser()
    assert data['error'] == 'not found'
    assert data['path'] == '/does-not-exist'


@pytest.mark.asyncio
async def test_on_exception_value_error():
    res = await client.get('/raise-value')
    assert res.status == 422
    data = res.parser()
    assert data['error'] == 'validation error'
    assert 'bad input' in data['detail']


@pytest.mark.asyncio
async def test_on_exception_runtime_error():
    res = await client.get('/raise-runtime')
    assert res.status == 500
    data = res.parser()
    assert data['error'] == 'runtime error'
    assert 'something broke' in data['detail']


@pytest.mark.asyncio
async def test_on_error_status_code():
    res = await client.get('/return-422')
    assert res.status == 422
    data = res.parser()
    assert data['error'] == 'unprocessable entity'


@pytest.mark.asyncio
async def test_unregistered_exception_uses_default():
    res = await client.get('/raise-custom')
    assert res.status == 400
    data = res.parser()
    assert 'detail' in data


@pytest.mark.asyncio
async def test_on_exception_mro_fallback():
    """Exception handler for a parent class should catch subclass exceptions."""
    app2 = Application()
    client2 = Client(app2)

    class AppError(Exception):
        pass

    class SpecificError(AppError):
        pass

    @app2.get('/fail')
    async def fail():
        raise SpecificError('oops')

    @app2.on_exception(AppError)
    async def handle_app_error(request: Request, exc: Exception):
        return Response({'caught': type(exc).__name__}, status=400)

    res = await client2.get('/fail')
    assert res.status == 400
    assert res.parser()['caught'] == 'SpecificError'


@pytest.mark.asyncio
async def test_on_error_handler_returns_tuple():
    app3 = Application()
    client3 = Client(app3)

    @app3.get('/missing')
    async def missing():
        pass

    @app3.on_error(404)
    async def custom_404(request: Request):
        return {'msg': 'gone'}, 410

    res = await client3.get('/not-there')
    assert res.status == 410
    assert res.parser()['msg'] == 'gone'


@pytest.mark.asyncio
async def test_on_error_handler_not_invoked_on_success():
    app4 = Application()
    client4 = Client(app4)
    invoked = []

    @app4.get('/good')
    async def good():
        return {'ok': True}

    @app4.on_error(404)
    async def track_404(request: Request):
        invoked.append(True)
        return Response({'error': 'not found'}, status=404)

    res = await client4.get('/good')
    assert res.status == 200
    assert not invoked
