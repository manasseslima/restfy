

class MockResponse:
    def __init__(self):
        self.status = 200


def mock_request(
    method,
    url,
    data,
    headers
):
    res = MockResponse
    return res
