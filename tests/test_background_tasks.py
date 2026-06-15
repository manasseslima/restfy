import asyncio
import pytest
from restfy import Application, Client, Request, Response, BackgroundTask, BackgroundTasks

app = Application()
client = Client(app)

log: list[str] = []


# --- helpers ---

async def async_record(msg: str):
    log.append(msg)


def sync_record(msg: str):
    log.append(msg)


# --- routes ---

@app.get('/inject')
async def inject_handler(tasks: BackgroundTasks):
    tasks.add(async_record, 'inject-async')
    return {'queued': True}


@app.get('/response-bg')
async def response_bg_handler():
    return Response(
        {'queued': True},
        background=BackgroundTask(async_record, 'response-async'),
    )


@app.get('/sync-task')
async def sync_task_handler():
    return Response({'ok': True}, background=BackgroundTask(sync_record, 'sync'))


@app.get('/both')
async def both_handler(tasks: BackgroundTasks):
    tasks.add(async_record, 'inject')
    return Response({'ok': True}, background=BackgroundTask(async_record, 'response'))


@app.get('/multi')
async def multi_handler(tasks: BackgroundTasks):
    tasks.add(async_record, 'first')
    tasks.add(async_record, 'second')
    return {'ok': True}


@app.get('/failing-task')
async def failing_task_handler():
    async def boom():
        raise RuntimeError('task failed')
    return Response({'ok': True}, background=BackgroundTask(boom))


# --- tests ---

@pytest.mark.asyncio
async def test_background_task_via_injection():
    log.clear()
    res = await client.get('/inject')
    assert res.status == 200
    assert res.parser() == {'queued': True}
    assert 'inject-async' in log


@pytest.mark.asyncio
async def test_background_task_via_response():
    log.clear()
    res = await client.get('/response-bg')
    assert res.status == 200
    assert 'response-async' in log


@pytest.mark.asyncio
async def test_sync_background_task():
    log.clear()
    res = await client.get('/sync-task')
    assert res.status == 200
    assert 'sync' in log


@pytest.mark.asyncio
async def test_both_injection_and_response_background():
    log.clear()
    res = await client.get('/both')
    assert res.status == 200
    assert 'inject' in log
    assert 'response' in log


@pytest.mark.asyncio
async def test_multiple_background_tasks():
    log.clear()
    res = await client.get('/multi')
    assert res.status == 200
    assert log == ['first', 'second']


@pytest.mark.asyncio
async def test_failing_task_does_not_break_response(capsys):
    res = await client.get('/failing-task')
    assert res.status == 200
    captured = capsys.readouterr()
    assert 'task failed' in captured.out


@pytest.mark.asyncio
async def test_background_tasks_run_after_response():
    """Tasks must not affect the response content."""
    log.clear()
    order: list[str] = []

    app2 = Application()
    client2 = Client(app2)

    @app2.get('/ordered')
    async def ordered(tasks: BackgroundTasks):
        order.append('handler')
        tasks.add(async_record, 'task')
        return {'ok': True}

    res = await client2.get('/ordered')
    assert res.status == 200
    assert order == ['handler']
    assert 'task' in log


@pytest.mark.asyncio
async def test_no_background_task_is_no_op():
    res = await client.get('/inject')
    assert res.status == 200


@pytest.mark.asyncio
async def test_background_task_direct():
    log.clear()
    task = BackgroundTask(async_record, 'direct')
    await task.run()
    assert 'direct' in log


@pytest.mark.asyncio
async def test_background_tasks_container():
    log.clear()
    tasks = BackgroundTasks()
    assert not tasks
    tasks.add(async_record, 'a')
    tasks.add(async_record, 'b')
    assert tasks
    await tasks.run()
    assert log == ['a', 'b']
