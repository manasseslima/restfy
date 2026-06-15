import asyncio
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from .response import Response


def _content_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or 'application/octet-stream'


def _etag(stat) -> str:
    return f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'


def _last_modified(stat) -> str:
    dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


async def serve_file(file_path: Path, request) -> Response:
    try:
        stat = file_path.stat()
    except (FileNotFoundError, PermissionError, OSError):
        return Response(status=404)

    etag = _etag(stat)
    last_modified = _last_modified(stat)

    if request.headers.get('If-None-Match') == etag:
        return Response(status=304)

    if_modified_since = request.headers.get('If-Modified-Since')
    if if_modified_since and 'If-None-Match' not in request.headers:
        try:
            from email.utils import parsedate_to_datetime
            ims = parsedate_to_datetime(if_modified_since)
            if datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc) <= ims:
                return Response(status=304)
        except Exception:
            pass

    content = await asyncio.to_thread(file_path.read_bytes)

    return Response(
        content,
        status=200,
        content_type=_content_type(file_path),
        headers={
            'ETag': etag,
            'Last-Modified': last_modified,
            'Cache-Control': 'public, max-age=3600',
        },
    )


async def handle_static(url_path: str, directory: str | Path, request) -> Response:
    root = Path(directory).resolve()
    rel = url_path.lstrip('/')
    target = (root / rel).resolve() if rel else root

    try:
        target.relative_to(root)
    except ValueError:
        return Response(status=403)

    if target.is_dir():
        index = target / 'index.html'
        if index.exists():
            target = index
        else:
            return Response(status=403)

    return await serve_file(target, request)
