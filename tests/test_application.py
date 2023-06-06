from restfy import Application
from restfy.testing import Client


def test_application_instantiation():
    app = Application(
        title='Test Application',
        description='Used by test'
    )
    assert app.title == 'Test Application'
    assert app.description == 'Used by test'






