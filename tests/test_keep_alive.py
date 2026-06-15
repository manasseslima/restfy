import asyncio
import json
import pytest
from restfy import Application, Client, Request
from restfy.connection import H1Connection

app = Application()
client = Client(app)


@app.get('/ping')
async def ping():
    return {'pong': True}


@app.post('/echo')
async def echo(request: Request):
    return request.data


# --- in-memory helpers (same pattern as test_websocket.py) ---

class MemoryWriter:
    def __init__(self, peer: asyncio.StreamReader):
        self._peer = peer
        self._closing = False

    def write(self, data: bytes):
        if not self._closing:
            self._peer.feed_data(data)

    async def drain(self):
        pass

    def is_closing(self):
        return self._closing

    def close(self):
        self._closing = True
        self._peer.feed_eof()

    async def wait_closed(self):
        pass


async def _make_connection():
    server_reader = asyncio.StreamReader()
    client_reader = asyncio.StreamReader()
    server_writer = MemoryWriter(client_reader)
    client_writer = MemoryWriter(server_reader)

    conn = H1Connection(reader=server_reader, writer=server_writer)
    conn.router = app.router
    conn.middlewares = app.middlewares
    conn.cors = app.cors
    conn.app = app
    app.connections[conn.id] = conn

    return conn, client_reader, client_writer


async def _read_response(client_reader: asyncio.StreamReader) -> tuple[int, dict, bytes]:
    """Read one HTTP response and return (status, headers, body)."""
    buf = b''
    while b'\r\n\r\n' not in buf:
        chunk = await asyncio.wait_for(client_reader.read(4096), timeout=2.0)
        if not chunk:
            break
        buf += chunk

    header_part, _, body_part = buf.partition(b'\r\n\r\n')
    lines = header_part.decode().split('\r\n')
    status = int(lines[0].split(' ')[1])
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            k, _, v = line.partition(':')
            headers[k.strip()] = v.strip()

    content_length = int(headers.get('Content-Length', 0))
    body = body_part
    while len(body) < content_length:
        body += await asyncio.wait_for(client_reader.read(content_length - len(body)), timeout=2.0)

    return status, headers, body


# --- tests ---

@pytest.mark.asyncio
async def test_keep_alive_two_requests():
    conn, client_reader, client_writer = await _make_connection()

    # First request headers (first line passed as data)
    client_writer.write(b'Host: localhost\r\n\r\n')
    # Second request (full — read by keep-alive loop)
    client_writer.write(b'GET /ping HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'GET /ping HTTP/1.1\r\n'))

    status1, headers1, body1 = await _read_response(client_reader)
    assert status1 == 200
    assert json.loads(body1) == {'pong': True}
    assert headers1.get('Connection') == 'keep-alive'

    status2, headers2, body2 = await _read_response(client_reader)
    assert status2 == 200
    assert json.loads(body2) == {'pong': True}
    assert headers2.get('Connection') == 'close'

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_keep_alive_response_headers():
    conn, client_reader, client_writer = await _make_connection()

    client_writer.write(b'Host: localhost\r\nConnection: close\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'GET /ping HTTP/1.1\r\n'))

    _, headers, _ = await _read_response(client_reader)
    assert headers.get('Connection') == 'close'

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_keep_alive_header_present():
    conn, client_reader, client_writer = await _make_connection()

    # Two requests so we get a keep-alive header on the first
    client_writer.write(b'Host: localhost\r\n\r\n')
    client_writer.write(b'GET /ping HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'GET /ping HTTP/1.1\r\n'))

    _, headers, _ = await _read_response(client_reader)
    assert 'Keep-Alive' in headers
    assert 'timeout=' in headers['Keep-Alive']

    await asyncio.wait_for(task, timeout=2.0)
    # drain second response
    await _read_response(client_reader)


@pytest.mark.asyncio
async def test_http10_default_close():
    conn, client_reader, client_writer = await _make_connection()

    client_writer.write(b'Host: localhost\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'GET /ping HTTP/1.0\r\n'))

    status, headers, body = await _read_response(client_reader)
    assert status == 200
    assert headers.get('Connection') == 'close'

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_http10_keep_alive():
    conn, client_reader, client_writer = await _make_connection()

    client_writer.write(b'Host: localhost\r\nConnection: keep-alive\r\n\r\n')
    client_writer.write(b'GET /ping HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'GET /ping HTTP/1.0\r\n'))

    status1, headers1, _ = await _read_response(client_reader)
    assert status1 == 200
    assert headers1.get('Connection') == 'keep-alive'

    status2, _, _ = await _read_response(client_reader)
    assert status2 == 200

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_keep_alive_post_then_get():
    conn, client_reader, client_writer = await _make_connection()

    body = b'{"msg":"hello"}'
    client_writer.write(
        b'Content-Type: application/json\r\n'
        + f'Content-Length: {len(body)}\r\n'.encode()
        + b'\r\n'
        + body
    )
    client_writer.write(b'GET /ping HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    client_writer.close()

    task = asyncio.ensure_future(conn.handler(b'POST /echo HTTP/1.1\r\n'))

    status1, _, body1 = await _read_response(client_reader)
    assert status1 == 200
    assert json.loads(body1) == {'msg': 'hello'}

    status2, _, _ = await _read_response(client_reader)
    assert status2 == 200

    await asyncio.wait_for(task, timeout=2.0)
