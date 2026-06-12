import asyncio
import json
import ssl
import subprocess

import pytest

from tests.acme.main import app


@pytest.fixture(scope='session')
def ssl_cert(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp('certs')
    cert = str(tmpdir / 'cert.pem')
    key = str(tmpdir / 'key.pem')
    subprocess.run(
        [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', key, '-out', cert,
            '-days', '1', '-nodes',
            '-subj', '/CN=localhost',
            '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1',
        ],
        check=True,
        capture_output=True,
    )
    return cert, key


async def _start_tls_server(cert: str, key: str):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    server = await asyncio.start_server(app.handler, '127.0.0.1', 0, ssl=ctx)
    port = server.sockets[0].getsockname()[1]
    return server, port


def _client_ctx(cert: str) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(cert)
    return ctx


async def _read_response(reader: asyncio.StreamReader, timeout: float = 5.0) -> bytes:
    # H1Connection fecha a conexão após responder — lemos até EOF
    response = b''
    try:
        while chunk := await asyncio.wait_for(reader.read(4096), timeout=timeout):
            response += chunk
    except asyncio.TimeoutError:
        pass
    return response


@pytest.mark.asyncio
async def test_https_get(ssl_cert):
    cert, key = ssl_cert
    server, port = await _start_tls_server(cert, key)

    async with server:
        reader, writer = await asyncio.open_connection(
            'localhost', port,
            ssl=_client_ctx(cert),
            server_hostname='localhost',
        )
        writer.write(b'GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n')
        await writer.drain()
        raw = await _read_response(reader)
        writer.close()
        await writer.wait_closed()

    lines = raw.decode().split('\r\n')
    assert lines[0] == 'HTTP/1.1 200 OK'
    body = json.loads(lines[-1])
    assert body['name'] == 'ACME API'


@pytest.mark.asyncio
async def test_https_post(ssl_cert):
    cert, key = ssl_cert
    server, port = await _start_tls_server(cert, key)

    async with server:
        reader, writer = await asyncio.open_connection(
            'localhost', port,
            ssl=_client_ctx(cert),
            server_hostname='localhost',
        )
        payload = json.dumps({'id': 99, 'name': 'test-https'}).encode()
        request = (
            f'POST /servers HTTP/1.1\r\n'
            f'Host: localhost\r\n'
            f'Content-Type: application/json\r\n'
            f'Content-Length: {len(payload)}\r\n'
            f'\r\n'
        ).encode() + payload
        writer.write(request)
        await writer.drain()
        raw = await _read_response(reader)
        writer.close()
        await writer.wait_closed()

    assert raw.decode().split('\r\n')[0] == 'HTTP/1.1 200 OK'
