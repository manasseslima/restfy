# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Fixed
- HTTP/2: duplicate `case b'\x02'` in `SettingFrame.set_payload()` — `SETTINGS_MAX_HEADER_LIST_SIZE` was never parsed (correct key: `b'\x06'`).
- HTTP/2: `TypeError` in `HeaderFrame.encode_payload()` when concatenating `int` to `bytes` (`md += i`).
- HTTP/2: `TypeError` in `HeaderFrame.encode_payload()` for short string values (≤ 5 chars) — `ec = val` kept a str instead of bytes.
- HTTP/2: dynamic table stored a tuple `(key, val)` but was consumed as a string, causing `AttributeError` on `.split()`.
- HTTP/2: missing Huffman flag `0x80` in the header name length byte in `encode_payload()`.
- HTTP/2: wrong slice in `validate_bulk()` — `bulk[9:fme.length - 9]` corrected to `bulk[9:9 + fme.length]`.
- HTTP/2: `H2Connection.handler()` only responded to `GET` requests; now uses `fme.end_stream` to cover `DELETE`, `HEAD` and other bodyless methods.
- Router: race condition under concurrent requests with path variables — `route.properties` was mutable shared state on the `Route` object. `match()` now returns `(route, args)` and args are written onto the per-request `request` object.
- Handler: falsy parameters (`0`, `False`, `""`) were silently dropped by `if not value`. Fixed to `if value is None`.
- Handler: `issubclass()` raised `TypeError` for modern type hints (`list[str]`, `dict[str, int]`, `str | None`). Added `inspect.isclass()` guard.
- Response: `bytes.encode()` does not exist — crash when returning binary data. `self.body` now keeps `bytes` as-is.
- Router: `register_router()` always referenced `self.variable` (root) when traversing intermediate variable nodes, ignoring the current traversal level.

### Added
- HTTPS integration tests (`test_https_get`, `test_https_post`) with a real TLS server, self-signed certificate and SSL client.
- WebSocket support: `WebSocket` class with `send_text`, `send_bytes`, `receive_text`, `receive_bytes`, `close`, fragmented-frame reassembly, auto-pong on ping, and RFC 6455 masking for client frames.
- WebSocket route handlers can now declare a `WebSocket` parameter; `Handler.execute_websocket()` injects it automatically alongside path/query args and the `Request`.
- `WebSocket` exported from the top-level `restfy` package.
- WebSocket integration tests (`test_websocket_text_echo`, `test_websocket_binary_echo`, `test_websocket_close_from_client`) using in-memory stream pairs.
- Configurable CORS via `CORSConfig` and `Application.configure_cors()`: `allow_origins` (list or `'*'`), `allow_methods`, `allow_headers`, `allow_credentials`, `max_age`, `expose_headers`. `CORSConfig` can also be passed directly to `Application(cors=...)`. `Vary: Origin` is added automatically when the response origin is not `*`.
- `CORSConfig` exported from the top-level `restfy` package.
- CORS tests covering wildcard, allowed/denied specific origins, preflight, credentials, and `CORSConfig` constructor injection.

### Fixed
- `websocket.prepare_websocket()`: `del response.headers[...]` raised `KeyError` when the header was absent; replaced with `.pop(..., None)`. Also removes `Content-Type` and `Content-Length` from 101 upgrade responses.
- `Connection.execute_handler()` now returns `(response, route)` so `H1Connection` can start the WebSocket message loop after sending the 101 response without re-matching the route.
- CORS: `AccessControl` used class-level variables, making all instances share the same configuration. Replaced with `CORSConfig` (instance variables).
- CORS: `allow_credentials=True` with wildcard origin is now forbidden per RFC — the response correctly echoes back the specific request origin instead of `*`.
- CORS: `expose_headers` was passed as a list object instead of a comma-separated string.
- CORS: preflight handling moved into `Connection.execute_handler()` so it works correctly via the testing `Client` (previously it was only in `H1Connection.handler`).

### Performance
- `H1Connection`: body reading replaced with `readexactly(length)`, eliminating the concatenation loop with 1000-byte chunks.
- `Request.args()`: removed redundant query string re-parsing; now returns `query_args` already populated by `generate_request()`.
- `Request.decode_data()`: result cached in `self.data`; subsequent calls to `dict()` no longer re-execute `json.loads()`.
- Router `add_node()`: `Handler` is now created only at the leaf node, eliminating discarded instances on intermediate nodes.
- Router `match()`: `while` + `list.pop(0)` (O(n) per step) replaced by `for node in nodes` (O(1)).


## [0.4.1] - 2023-06-09
### Added
- New Request attributes vars and params to get path variables and query string parameters respectively.

### Updated
- Documentation with model information.

### Fixed
- Fixed routers with variable errors. 

## [0.4.0] - 2023-05-31
### Add
- Application has a title and description attribute.
- New method .parser() in Response class to get dict, list or a model instance.
- New module testing with Client class to provide tests.
- Using bike like model processor.
- HTTPS support.
- HTTP request client to requests.

### Fixed
- Registering handler not mapping root paths.


## [0.3.1] - 2022-03-11
### Added
- Response use specialized class to encoder json.

### Fixed
- Fixed error when create a handler without Request return type information.


## [0.3.0] - 2022-03-03
### Added
- Register subrouters with a base path node.
- Application with CORS configuration.
- Application instance in request instance.
- Multipart Form data extract to data and files request attributes.
- URL form encoded data.
- Prepare request data before execute handler.
- Application and Router with decorator route add.

## [0.2.0] - 2022-02-23
### Added
- A Server class to run an Application instance.
- Path variables to routes using name into {}.
- Request method .dict() to parser body to dict.
- Request method .args() to parser querystring variables to dict.
- Print requests info.


## [0.1.0] - 2017-02-16
### Added
- Class Application to execute requests.
- Class Request to organize HTTP request elements.
- Class Response to render an HTTP response format.
- Created router handlers.



[Unreleased]: https://github.com/manasseslima/restfy/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/manasseslima/restfy/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/manasseslima/restfy/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/manasseslima/restfy/compare/v0.3.1...v0.3.0
[0.3.0]: https://github.com/manasseslima/restfy/compare/v0.3.0...v0.2.0
[0.2.0]: https://github.com/manasseslima/restfy/compare/v0.2.0...v0.1.0
[0.1.0]: https://github.com/manasseslima/restfy/releases/tag/v0.0.1
