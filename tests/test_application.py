from restfy import Application
from restfy.testing import Client


async def test_application_instantialization():
    app = Application(
        title='Test Application',
        description='Used by test'
    )
    assert app.title == 'Test Application'






