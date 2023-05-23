from restfy import Application


app = Application(
    title='Test Application',
    description='Used by test'
)


@app.get('/')
async def root_handler():
    return "root"


@app.get('/servers')
async def get_servers_list():
    servers = [
        {
            'id': 1,
            'name': 'Hotbike'
        },
        {
            'id': 2,
            'name': 'SimpleSky'
        }
    ]
    return servers
