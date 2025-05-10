import enum
import queue
import uuid
from collections import deque
from typing import Any

from .huffman import decode_huffman_code, encode_data_ruffman


static_table = {
    1: 'authority',
    2: 'method:GET',
    3: 'method:POST',
    4: 'path:/',
    5: 'path:/index.html',
    6: 'scheme:http',
    7: 'scheme:https',
    8: 'status:200',
    9: 'status:204',
    10: 'status:206',
    11: 'status:304',
    12: 'status:400',
    13: 'status:404',
    14: 'status:500',
    15: 'accept-charset',
    16: 'accept-encoding:gzip, deflate',
    17: 'accept-language',
    18: 'accept-ranges',
    19: 'accept',
    20: 'access-control-allow-origin',
    21: 'age',
    22: 'allow',
    23: 'authorization',
    24: 'cache-control',
    25: 'content-disposition',
    26: 'content-encoding',
    27: 'content-language',
    28: 'content-length',
    29: 'content-location',
    30: 'content-range',
    31: 'content-type',
    32: 'cookie',
    33: 'date',
    34: 'etag',
    35: 'expect',
    36: 'expires',
    37: 'from',
    38: 'host',
    39: 'if-match',
    40: 'if-modified-since',
    41: 'if-none-match',
    42: 'if-range',
    43: 'if-unmodified-since',
    44: 'last-modified',
    45: 'link',
    46: 'location',
    47: 'max-forwards',
    48: 'proxy-authenticate',
    49: 'proxy-authorization',
    50: 'range',
    51: 'referer',
    52: 'refresh',
    53: 'retry-after',
    54: 'server',
    55: 'set-cookie',
    56: 'strict-transport-security',
    57: 'transfer-encoding',
    58: 'user-agent',
    59: 'vary',
    60: 'via',
    61: 'www-authenticate',
}

static_table_code = {
    'authority': 1,
    'method:GET': 2,
    'method:POST': 3,
    'path:/': 4,
    'path:/index.html': 5,
    'scheme:http': 6,
    'scheme:https': 7,
    'status:200': 8,
    'status:204': 9,
    'status:206': 10,
    'status:304': 11,
    'status:400': 12,
    'status:404': 13,
    'status:500': 14,
    'accept-charset': 15,
    'accept-encoding:gzip, deflate': 16,
    'accept-language': 17,
    'accept-ranges': 18,
    'accept': 19,
    'access-control-allow-origin': 20,
    'age': 21,
    'allow': 22,
    'authorization': 23,
    'cache-control': 24,
    'content-disposition': 25,
    'content-encoding': 26,
    'content-language': 27,
    'content-length': 28,
    'content-location': 29,
    'content-range': 30,
    'content-type': 31,
    'cookie': 32,
    'date': 33,
    'etag': 34,
    'expect': 35,
    'expires': 36,
    'from': 37,
    'host': 38,
    'if-match': 39,
    'if-modified-since': 40,
    'if-none-match': 41,
    'if-range': 42,
    'if-unmodified-since': 43,
    'last-modified': 44,
    'link': 45,
    'location': 46,
    'max-forwards': 47,
    'proxy-authenticate': 48,
    'proxy-authorization': 49,
    'range': 50,
    'referer': 51,
    'refresh': 52,
    'retry-after': 53,
    'server': 54,
    'set-cookie': 55,
    'strict-transport-security': 56,
    'transfer-encoding': 57,
    'user-agent': 58,
    'vary': 59,
    'via': 60,
    'www-authenticate': 61,
}


class Frame:
    length: int
    type: int
    flags: int
    stream: int
    payload_size: int
    payload: ...

    def __init__(self, length: bytes, flags: int, stream: bytes, connection: Any):
        self.id = str(uuid.uuid4())
        self.length = int.from_bytes(length, byteorder='big', signed=False)
        self.flags = flags
        self.stream = int.from_bytes(stream, byteorder='big', signed=False)
        self.payload = None
        self.connection = connection
        ...

    def __str__(self):
        return f'{self.__class__.__name__}:{self.length}'

    def __repr__(self):
        return f'{self.__class__.__name__}:{self.length}'

    def set_payload(self, chunk: bytes):
        ...

    def generate(self) -> bytes:
        ret = b''
        ret += self.length.to_bytes(3, byteorder='big', signed=False)
        ret += self.type.to_bytes(1, byteorder='big', signed=False)
        ret += self.flags.to_bytes(1, byteorder='big', signed=False)
        ret += self.stream.to_bytes(4, byteorder='big', signed=False)
        return ret


class SettingConfig:
    header_table_size = 4096
    enable_push = 0
    max_concurrent_streams = 0
    initial_window_size = 65535
    max_frame_size = 16384
    max_header_list_size = 0


class SettingsEnum(enum.Enum):
    SETTINGS_HEADER_TABLE_SIZE = b'\x01'
    SETTINGS_ENABLE_PUSH = b'\x02'
    SETTINGS_MAX_CONCURRENT_STREAMS = b'\x03'
    SETTINGS_INITIAL_WINDOW_SIZE = b'\x04'
    SETTINGS_MAX_FRAME_SIZE = b'\x05'
    SETTINGS_MAX_HEADER_LIST_SIZE = b'\x06'


class DataFrame(Frame):
    """
    DATA Frame {
      Length (24),
      Type (8) = 0x00,

      Unused Flags (4),
      PADDED Flag (1),
      Unused Flags (2),
      END_STREAM Flag (1),

      Reserved (1),
      Stream Identifier (31),

      [Pad Length (8)],
      Data (..),
      Padding (..2040),
    }
    """
    type = 0x00
    end_stream = False
    padded = False

    def __init__(self, length: bytes, flags: int, stream: bytes, connection: Any):
        super().__init__(length, flags, stream, connection)
        self.padded = bool(0b00001000 & self.flags)
        self.end_stream = bool(0b00000001 & self.flags)
        ...

    def set_payload(self, value: bytes):
        body = value
        self.payload = body

    def generate(self) -> bytes:
        ret = super().generate()
        ret += self.payload
        return ret


class HeaderFrame(Frame):
    """
    HEADERS Frame {
      Length (24),
      Type (8) = 0x01,

      Unused Flags (2),
      PRIORITY Flag (1),
      Unused Flag (1),
      PADDED Flag (1),
      END_HEADERS Flag (1),
      Unused Flag (1),
      END_STREAM Flag (1),
      ex: __1_11_1

      Reserved (1),
      Stream Identifier (31),

      -- payload
      [Pad Length (8)],             ONLY PAD FLAG
      [Exclusive (1)],              ONLY PRIORITY FLAG
      [Stream Dependency (31)],     0NLY PRIORITY FLAG
      [Weight (8)],                 ONLY PRIORITY FLAG
      Field Block Fragment (..),
      Padding (..2040),
    }
    """
    type = 0x01
    priority = False
    padded = False
    end_headers = False
    end_stream = False

    def __init__(self, length: bytes, flags: int, stream: bytes, connection: Any):
        super().__init__(length, flags, stream, connection)
        self.priority = bool(0b0010000 & self.flags)
        self.padded = bool(0b00001000 & self.flags)
        self.end_headers = bool(0b00000100 & self.flags)
        self.end_stream = bool(0b00000001 & self.flags)

    def set_payload(self, value: bytes):
        self.payload = self.decode_payload(value=value)

    def decode_payload(self, value: bytes):
        headers = {}
        p = 0
        while True:
            bc = value[p]
            if bc == 15:
                p += 1
                pc = value[p]
                bc += pc
            bits = f'{bin(bc)[2:]:0>8}'
            mode = bits[:2]
            code = bits[2:]
            key_code = int(code, 2)
            if key_code > 61:
                key = self.connection.get_dynamic_table_element(key_code)
            else:
                key = static_table.get(key_code, '')
            if mode == '10':
                if key:
                    splt = key.split(':')
                    if len(splt) > 1:
                        headers[splt[0]] = splt[1]
                p += 1
            else:
                nk = True if not key else False
                if nk:
                    p += 1
                    bs = value[p]
                    bits_bs = f'{bin(bs)[2:]:0>8}'
                    mode_bs = bits_bs[:1]
                    size = int(bits_bs[1:], 2)
                    p += 1
                    t = p + size
                    v = value[p: t]
                    key = decode_huffman_code(v)
                    p = t
                else:
                    p += 1
                bs = value[p]
                bits_bs = f'{bin(bs)[2:]:0>8}'
                mode_bs = bits_bs[:1]
                size = int(bits_bs[1:], 2)
                p += 1
                t = p + size
                v = value[p: t]
                if mode_bs == '0':
                    if mode == '00':
                        val_bs = int.from_bytes(v)
                    else:
                        val_bs = v.decode()
                else:
                    val_bs = decode_huffman_code(v)
                p = t
                splt = key.split(':', maxsplit=1)
                headers[splt[0]] = val_bs
                if mode == '01':
                    self.connection.add_dynamic_table_element((key, val_bs))
            if p >= len(value):
                break
        return headers

    def encode_payload(self) -> bytes:
        ret = b''
        dtk = {
            'status': [200, 204, 206, 304, 400, 404, 500] ,
            'location': [], 
            'date': [], 
            'cache-control': []
        }
        for k, val in self.payload.items():
            key = k.lower()
            typo = 64 if isinstance(val, str) else 0
            if key in dtk and val in dtk[key]:
                key_val = f'{key}:{val}'
                typo = 128
                code = static_table_code.get(key_val, '')
                ec = (128 + code).to_bytes(1)
                ret += ec
                continue
            else:
                code = static_table_code.get(key, '')
            if not code:
                ec = encode_data_ruffman(key)
                sz = (0).to_bytes(1, 'big', signed=False)
                ret += sz
                sz = (len(ec)).to_bytes(1, 'big', signed=False)
                ret += sz
                ret += ec
            else:
                if code > 31:
                    typo = 64
                    md = (typo + 31).to_bytes(1, 'big', signed=False)
                    i = code - 31
                    if i >= 128:
                        rt = (i % 128).to_bytes(1, 'big', signed=False)
                        ml = (128 + (i // 128)).to_bytes(1, 'big', signed=False)
                        md += ml + rt
                    else:
                        md += i
                else:
                    md = (typo + code).to_bytes(1, 'big', signed=False)
                ret += md
            if isinstance(val, str):
                if len(val) > 5:
                    ec = encode_data_ruffman(val)
                    typo = 128
                else:
                    ec = val
                    typo = 0
                sz = (typo + len(ec)).to_bytes(1, 'big', signed=False)
                ret += sz
                ret += ec
            else:
                if val < 128:
                    bv = val.to_bytes(1, 'big', signed=False)
                    sz = len(bv)
                    ret += sz.to_bytes(1, 'big', signed=False)
                    ret += bv
                else:
                    pre = val - 31
                    ret += int(31).to_bytes(1, 'big', signed=False)
                    if pre < 128:
                        ret += pre.to_bytes(1, 'big', signed=False)
                    else:
                        rst = pre % 128
                        mul = pre // 128
                        while mul >= 128:
                            mul -= 127
                            ret += (128 + 127).to_bytes(1, 'big', signed=False)
                        ret += mul.to_bytes(1, 'big', signed=False)
                        ret += rst.to_bytes(1, 'big', signed=False)
        if ret:
            p = self.decode_payload(ret)
        return ret

    def generate(self) -> bytes:
        enc = self.encode_payload()
        self.length = len(enc)
        hea = super().generate()
        block = hea + enc
        return block


class PriorityFrame(Frame):
    """
    PRIORITY Frame {
      Length (24) = 0x05,
      Type (8) = 0x02,

      Unused Flags (8),

      Reserved (1),
      Stream Identifier (31),

      Exclusive (1),
      Stream Dependency (31),
      Weight (8),
    }
    """
    type = 0x02


class RSTStreamFrame(Frame):
    """
    RST_STREAM Frame {
      Length (24) = 0x04,
      Type (8) = 0x03,

      Unused Flags (8),

      Reserved (1),
      Stream Identifier (31),

      Error Code (32),
    }
    """
    type = 0x03


class SettingFrame(Frame):
    """
    SETTINGS Frame {
      Length (24),
      Type (8) = 0x04,

      Unused Flags (7),
      ACK Flag (1),

      Reserved (1),
      Stream Identifier (31) = 0,

      Setting (48) ...,
    }

    Setting {
      Identifier (16),
      Value (32),
    }
    """
    type = 0x04
    payload_size = 6
    payload: SettingConfig

    def set_payload(self, value: bytes):
        self.payload = SettingConfig()
        p = 0
        while p < len(value):
            k = value[p + 1:p + 2]
            v = value[p + 2:p + 6]
            match k:
                case b'\x01':
                    self.payload.header_table_size = int.from_bytes(v)
                case b'\x02':
                    self.payload.enable_push = v == b'\x00\x00\x00\x01'
                case b'\x03':
                    self.payload.max_concurrent_streams = int.from_bytes(v)
                case b'\x04':
                    self.payload.initial_window_size = int.from_bytes(v)
                case b'\x05':
                    self.payload.max_frame_size = int.from_bytes(v)
                case b'\x02':
                    self.payload.max_header_list_size = int.from_bytes(v)
            p += 6


class PushPromisseFrame(Frame):
    """
    PUSH_PROMISE Frame {
      Length (24),
      Type (8) = 0x05,

      Unused Flags (4),
      PADDED Flag (1),
      END_HEADERS Flag (1),
      Unused Flags (2),

      Reserved (1),
      Stream Identifier (31),

      [Pad Length (8)],
      Reserved (1),
      Promised Stream ID (31),
      Field Block Fragment (..),
      Padding (..2040),
    }'
    """
    type = 0x05


class PingFrame(Frame):
    """
    PING Frame {
      Length (24) = 0x08,
      Type (8) = 0x06,

      Unused Flags (7),
      ACK Flag (1),

      Reserved (1),
      Stream Identifier (31) = 0,

      Opaque Data (64),
    }
    """
    type = 0x06


class GoawayFrame(Frame):
    """
    GOAWAY Frame {
      Length (24),
      Type (8) = 0x07,

      Unused Flags (8),

      Reserved (1),
      Stream Identifier (31) = 0,

      Reserved (1),
      Last-Stream-ID (31),
      Error Code (32),
      Additional Debug Data (..),
    }
    """
    type = 0x07


class WindowUpdateFrame(Frame):
    """
    WINDOW_UPDATE Frame {
      Length (24) = 0x04,
      Type (8) = 0x08,

      Unused Flags (8),

      Reserved (1),
      Stream Identifier (31),

      Reserved (1),
      Window Size Increment (31),
    }
    """
    type = 0x08

    def set_payload(self, value: bytes):
        self.payload = int.from_bytes(value)


class ContinuationFrame(Frame):
    """
    CONTINUATION Frame {
      Length (24),
      Type (8) = 0x09,

      Unused Flags (5),
      END_HEADERS Flag (1),
      Unused Flags (2),

      Reserved (1),
      Stream Identifier (31),

      Field Block Fragment (..),
    }
    """
    type = 0x09
