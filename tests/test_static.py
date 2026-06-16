import asyncio
import os
import tempfile
import pytest
from pathlib import Path
from restfy import Application, Client


def make_app(tmp_path: Path) -> tuple[Application, Client]:
    app = Application()
    app.mount_static('/static', directory=str(tmp_path))
    return app, Client(app)


# --- tests ---

@pytest.mark.asyncio
async def test_serve_text_file(tmp_path):
    (tmp_path / 'hello.txt').write_text('Hello, world!')
    app, client = make_app(tmp_path)
    res = await client.get('/static/hello.txt')
    assert res.status == 200
    assert res.body == b'Hello, world!'
    assert 'text/plain' in res.headers.get('Content-Type', '')


@pytest.mark.asyncio
async def test_serve_html_file(tmp_path):
    (tmp_path / 'page.html').write_text('<h1>Hi</h1>')
    app, client = make_app(tmp_path)
    res = await client.get('/static/page.html')
    assert res.status == 200
    assert b'<h1>Hi</h1>' in res.body
    assert 'html' in res.headers.get('Content-Type', '')


@pytest.mark.asyncio
async def test_serve_css_file(tmp_path):
    (tmp_path / 'style.css').write_text('body { color: red; }')
    app, client = make_app(tmp_path)
    res = await client.get('/static/style.css')
    assert res.status == 200
    assert 'css' in res.headers.get('Content-Type', '')


@pytest.mark.asyncio
async def test_serve_json_file(tmp_path):
    (tmp_path / 'data.json').write_text('{"key": "value"}')
    app, client = make_app(tmp_path)
    res = await client.get('/static/data.json')
    assert res.status == 200
    assert 'json' in res.headers.get('Content-Type', '')


@pytest.mark.asyncio
async def test_file_not_found_returns_404(tmp_path):
    app, client = make_app(tmp_path)
    res = await client.get('/static/missing.txt')
    assert res.status == 404


@pytest.mark.asyncio
async def test_directory_without_index_returns_403(tmp_path):
    subdir = tmp_path / 'assets'
    subdir.mkdir()
    app, client = make_app(tmp_path)
    res = await client.get('/static/assets')
    assert res.status == 403


@pytest.mark.asyncio
async def test_directory_with_index_html(tmp_path):
    subdir = tmp_path / 'app'
    subdir.mkdir()
    (subdir / 'index.html').write_text('<html>Index</html>')
    app, client = make_app(tmp_path)
    res = await client.get('/static/app')
    assert res.status == 200
    assert b'Index' in res.body


@pytest.mark.asyncio
async def test_path_traversal_returns_403(tmp_path):
    secret = tmp_path.parent / 'secret.txt'
    secret.write_text('secret')
    app, client = make_app(tmp_path)
    res = await client.get('/static/../secret.txt')
    assert res.status in (403, 404)
    secret.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_etag_header_present(tmp_path):
    (tmp_path / 'asset.js').write_text('console.log(1)')
    app, client = make_app(tmp_path)
    res = await client.get('/static/asset.js')
    assert res.status == 200
    assert 'ETag' in res.headers


@pytest.mark.asyncio
async def test_not_modified_with_etag(tmp_path):
    (tmp_path / 'cached.txt').write_text('data')
    app, client = make_app(tmp_path)
    first = await client.get('/static/cached.txt')
    assert first.status == 200
    etag = first.headers.get('ETag', '')
    assert etag
    second = await client.get('/static/cached.txt', headers={'If-None-Match': etag})
    assert second.status == 304


@pytest.mark.asyncio
async def test_last_modified_header_present(tmp_path):
    (tmp_path / 'file.txt').write_text('data')
    app, client = make_app(tmp_path)
    res = await client.get('/static/file.txt')
    assert res.status == 200
    assert 'Last-Modified' in res.headers


@pytest.mark.asyncio
async def test_cache_control_header(tmp_path):
    (tmp_path / 'img.png').write_bytes(b'\x89PNG\r\n\x1a\n')
    app, client = make_app(tmp_path)
    res = await client.get('/static/img.png')
    assert res.status == 200
    assert 'Cache-Control' in res.headers


@pytest.mark.asyncio
async def test_binary_pdf_content_type(tmp_path):
    (tmp_path / 'doc.pdf').write_bytes(b'%PDF-1.4 content')
    app, client = make_app(tmp_path)
    res = await client.get('/static/doc.pdf')
    assert res.status == 200
    assert 'pdf' in res.headers.get('Content-Type', '').lower()


@pytest.mark.asyncio
async def test_mount_prefix_exact_match(tmp_path):
    (tmp_path / 'index.html').write_text('<html/>')
    app, client = make_app(tmp_path)
    res = await client.get('/static')
    assert res.status == 200


@pytest.mark.asyncio
async def test_static_does_not_shadow_api_routes(tmp_path):
    app, client = make_app(tmp_path)

    @app.get('/api/ping')
    async def ping():
        return {'pong': True}

    res = await client.get('/api/ping')
    assert res.status == 200
    assert res.parser() == {'pong': True}


@pytest.mark.asyncio
async def test_static_file_in_subdirectory(tmp_path):
    subdir = tmp_path / 'js'
    subdir.mkdir()
    (subdir / 'app.js').write_text('var x = 1;')
    app, client = make_app(tmp_path)
    res = await client.get('/static/js/app.js')
    assert res.status == 200
    assert res.body == b'var x = 1;'
