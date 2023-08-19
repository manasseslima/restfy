import enum
import uuid
from .huffman import decode_huffman_code


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


def get_frame(frame_header: bytes):
    frame = {
        0: DataFrame,
        1: HeaderFrame,
        2: PriorityFrame,
        3: RSTStreamFrame,
        4: SettingFrame,
        5: PushPromisseFrame,
        6: PingFrame,
        7: GoawayFrame,
        8: WindowUpdateFrame,
        9: ContinuationFrame,
    }.get(frame_header[3], Frame)(
        length=frame_header[:3],
        flags=frame_header[4],
        stream=frame_header[5:]
    )
    return frame


class Frame:
    length: int
    type: int
    flags: int
    stream: int
    payload_size: int

    def __init__(self, length: bytes, flags: chr, stream: bytes):
        self.id = uuid.uuid4()
        self.length = int.from_bytes(length, byteorder='big', signed=False)
        self.flags = flags
        self.stream = int.from_bytes(stream, byteorder='big', signed=False)
        ...

    def __str__(self):
        return f'{self.__class__.__name__}:{self.length}'

    def __repr__(self):
        return f'{self.__class__.__name__}:{self.length}'

    def set_payload(self, chunk: bytes):
        ...


class SettingPayload:
    def __init__(self, identifier: bytes, value: bytes):
        self.identifier = identifier
        self.value = value


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

    def set_payload(self, value: bytes):
        ...


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

    def set_payload(self, value: bytes):
        headers = {}
        p = 0
        while True:
            bc = value[p]
            bits = f'{str(bin(bc))[2:]:0>8}'
            mode = bits[:2]
            code = bits[2:]
            val = static_table.get(int(code, 2), '')
            if mode == '10':
                if val:
                    splt = val.split(':')
                    if len(splt) > 1:
                        headers[splt[0]] = splt[1]
                p += 1
            else:
                p += 1
                bs = value[p]
                bits_bs = f'{str(bin(bs))[2:]:0>8}'
                mode_bs = bits_bs[:2]
                size = int(bits_bs[2:], 2)
                p += 1
                t = p + size
                v = value[p: t]
                if mode_bs == '00':
                    val_bs = v.decode()
                else:
                    val_bs = decode_huffman_code(v)
                p = t
                splt = val.split(':')
                headers[splt[0]] = val_bs
            if p >= len(value):
                break
        ...


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
    payload: SettingPayload
    payload_size = 6

    def set_payload(self, value: bytes):
        payload = SettingPayload(
            identifier=value[:2],
            value=value[2:]
        )
        self.payload = payload


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
