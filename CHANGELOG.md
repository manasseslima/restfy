# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Register subrouters with a base path node.

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



[Unreleased]: https://github.com/manasseslima/restfy/compare/v0.3.0...HEAD
[0.2.0]: https://github.com/manasseslima/restfy/compare/v0.2.0...v0.1.0
[0.1.0]: https://github.com/manasseslima/restfy/releases/tag/v0.0.1
