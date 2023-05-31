from unittest import mock
import pytest
import httplus
from restfy import http
from .mocks import MockResponse


@mock.patch.object(httplus.Client, 'request', return_value=MockResponse())
@pytest.mark.asyncio
async def test_http_get_request(obj1):
    res = await http.get('http://mockserver.mock/api/servers')
    assert res.status == 200
