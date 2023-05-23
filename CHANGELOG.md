# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Add
- Application has a title and description attribute.
- New method .parser() in Response class to get dict, list or a model instance.
- New module testing with Client class to provide tests.
### Fixed


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



[Unreleased]: https://github.com/manasseslima/restfy/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/manasseslima/restfy/compare/v0.3.1...v0.3.0
[0.3.0]: https://github.com/manasseslima/restfy/compare/v0.3.0...v0.2.0
[0.2.0]: https://github.com/manasseslima/restfy/compare/v0.2.0...v0.1.0
[0.1.0]: https://github.com/manasseslima/restfy/releases/tag/v0.0.1
