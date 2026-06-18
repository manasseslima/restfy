import asyncio
import base64
import hashlib
import struct

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


class WebSocket:
    def __init__(self, reader: asyncio.StreamReader, writer):
        self.reader = reader
        self.writer = writer
        self.closed = False

    async def send_text(self, text: str):
        await self._send_frame(OPCODE_TEXT, text.encode('utf-8'))

    async def send_bytes(self, data: bytes):
        await self._send_frame(OPCODE_BINARY, data)

    async def receive(self) -> tuple[int, bytes]:
        return await self._read_message()

    async def receive_text(self) -> str:
        opcode, payload = await self._read_message()
        return payload.decode('utf-8')

    async def receive_bytes(self) -> bytes:
        _, payload = await self._read_message()
        return payload

    async def close(self, code: int = 1000, reason: str = ''):
        if not self.closed:
            self.closed = True
            payload = struct.pack('>H', code) + reason.encode('utf-8')
            await self._send_frame(OPCODE_CLOSE, payload)

    def _encode_frame(self, opcode: int, payload: bytes) -> bytes:
        fin_opcode = 0x80 | opcode
        length = len(payload)
        if length < 126:
            header = bytes([fin_opcode, length])
        elif length < 65536:
            header = bytes([fin_opcode, 126]) + struct.pack('>H', length)
        else:
            header = bytes([fin_opcode, 127]) + struct.pack('>Q', length)
        return header + payload

    async def _send_frame(self, opcode: int, payload: bytes):
        self.writer.write(self._encode_frame(opcode, payload))
        await self.writer.drain()

    async def _read_frame(self) -> tuple[bool, int, bytes]:
        header = await self.reader.readexactly(2)
        fin = bool(header[0] & 0x80)
        opcode = header[0] & 0x0F
        masked = bool(header[1] & 0x80)
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack('>H', await self.reader.readexactly(2))[0]
        elif length == 127:
            length = struct.unpack('>Q', await self.reader.readexactly(8))[0]
        if masked:
            mask_key = await self.reader.readexactly(4)
            raw = bytearray(await self.reader.readexactly(length))
            for i in range(length):
                raw[i] ^= mask_key[i % 4]
            payload = bytes(raw)
        else:
            payload = await self.reader.readexactly(length)
        return fin, opcode, payload

    async def _read_message(self) -> tuple[int, bytes]:
        fragments = []
        message_opcode = None
        while True:
            fin, opcode, payload = await self._read_frame()
            if opcode == OPCODE_PING:
                await self._send_frame(OPCODE_PONG, payload)
                continue
            if opcode == OPCODE_PONG:
                continue
            if opcode == OPCODE_CLOSE:
                self.closed = True
                if not self.writer.is_closing():
                    await self._send_frame(OPCODE_CLOSE, payload)
                raise ConnectionError('WebSocket connection closed by client')
            if opcode != OPCODE_CONTINUATION:
                message_opcode = opcode
            fragments.append(payload)
            if fin:
                return message_opcode, b''.join(fragments)


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
    response.headers.pop('Content-Type', None)
    response.headers.pop('Content-Length', None)
    response.headers.pop('Access-Control-Allow-Origin', None)
    response.headers.update(ws_header)
