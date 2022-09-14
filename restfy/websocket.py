import base64
import hashlib


def prepare_websocket(request, response):
    uid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    key = request.headers.get('Sec-WebSocket-Key')
    new_key = key + uid
    sha = hashlib.sha1(new_key.encode()).digest()
    accept = base64.b64encode(sha).decode()
    ws_header = {
        'Upgrade': request.headers.get('Upgrade'),
        'Connection': request.headers.get('Connection'),
        'Sec-WebSocket-Accept': accept,
    }
    if 'Sec-WebSocket-Protocol' in request.headers:
        ws_header['Sec-WebSocket-Protocol'] = request.headers['Sec-WebSocket-Protocol']
    response.status = 101
    del response.headers['Access-Control-Allow-Origin']
    response.headers.update(ws_header)
