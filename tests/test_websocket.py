import asyncio
import base64
import struct
import pytest
from restfy import Application, Request, WebSocket
from restfy.connection import H1Connection

app = Application()


@app.websocket('/chat')
async def chat_handler(ws: WebSocket, request: Request):
    text = await ws.receive_text()
    await ws.send_text(f'echo:{text}')


@app.websocket('/binary')
async def binary_handler(ws: WebSocket):
    data = await ws.receive_bytes()
    await ws.send_bytes(data)


@app.websocket('/loop')
async def loop_handler(ws: WebSocket):
    while True:
        text = await ws.receive_text()
        await ws.send_text(text)


class MemoryWriter:
    """In-memory writer that feeds data directly into a peer StreamReader."""

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


def _client_frame(payload: bytes, opcode: int = 0x1) -> bytes:
    mask = b'\x01\x02\x03\x04'
    masked = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
    return bytes([0x80 | opcode, 0x80 | len(payload)]) + mask + masked


def _close_frame() -> bytes:
    mask = b'\x00\x00\x00\x00'
    payload = struct.pack('>H', 1000)
    masked = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
    return bytes([0x88, 0x80 | len(payload)]) + mask + masked


async def _make_connection():
    server_reader = asyncio.StreamReader()
    client_reader = asyncio.StreamReader()
    server_writer = MemoryWriter(client_reader)
    client_writer = MemoryWriter(server_reader)

    conn = H1Connection(reader=server_reader, writer=server_writer)
    conn.router = app.router
    conn.middlewares = app.middlewares
    conn.app = app
    app.connections[conn.id] = conn

    return conn, client_reader, client_writer


async def _do_handshake(conn, client_reader, client_writer, path):
    key = base64.b64encode(b'test-key-1234567').decode()
    client_writer.write(
        b'Host: localhost\r\n'
        b'Upgrade: websocket\r\n'
        b'Connection: Upgrade\r\n'
        + f'Sec-WebSocket-Key: {key}\r\n'.encode()
        + b'Sec-WebSocket-Version: 13\r\n'
        + b'\r\n'
    )

    first_line = f'GET {path} HTTP/1.1\r\n'.encode()
    task = asyncio.ensure_future(conn.handler(first_line))

    buf = b''
    while b'\r\n\r\n' not in buf:
        buf += await asyncio.wait_for(client_reader.read(256), timeout=2.0)

    assert b'101' in buf
    assert b'Sec-WebSocket-Accept' in buf
    return task


@pytest.mark.asyncio
async def test_websocket_text_echo():
    conn, client_reader, client_writer = await _make_connection()
    task = await _do_handshake(conn, client_reader, client_writer, '/chat')

    client_writer.write(_client_frame(b'hello'))

    header = await asyncio.wait_for(client_reader.readexactly(2), timeout=2.0)
    assert header[0] == 0x81  # FIN + text opcode
    payload = await asyncio.wait_for(client_reader.readexactly(header[1]), timeout=2.0)
    assert payload == b'echo:hello'

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_websocket_binary_echo():
    conn, client_reader, client_writer = await _make_connection()
    task = await _do_handshake(conn, client_reader, client_writer, '/binary')

    data = b'\x00\x01\x02\x03'
    client_writer.write(_client_frame(data, opcode=0x2))

    header = await asyncio.wait_for(client_reader.readexactly(2), timeout=2.0)
    assert header[0] == 0x82  # FIN + binary opcode
    payload = await asyncio.wait_for(client_reader.readexactly(header[1]), timeout=2.0)
    assert payload == data

    await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_websocket_close_from_client():
    conn, client_reader, client_writer = await _make_connection()
    task = await _do_handshake(conn, client_reader, client_writer, '/loop')

    client_writer.write(_client_frame(b'hi'))
    header = await asyncio.wait_for(client_reader.readexactly(2), timeout=2.0)
    await asyncio.wait_for(client_reader.readexactly(header[1]), timeout=2.0)

    client_writer.write(_close_frame())

    close_header = await asyncio.wait_for(client_reader.readexactly(2), timeout=2.0)
    assert close_header[0] == 0x88  # FIN + close opcode

    await asyncio.wait_for(task, timeout=2.0)
