from restfy import Application, Client


async def teste_client_application():
    app = Application(
        title='Test Application',
        description='Used by test'
    )

    async def root_handler():
        return "oi"

    app.add_route('/', root_handler, 'GET')

    client = Client(app)
    res = await client.get('/')
    assert res.status_code == 200
