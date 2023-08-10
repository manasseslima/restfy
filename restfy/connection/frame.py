import enum


class Frame:
    length: int
    type: int
    flags: int
    identifier: int
    payload_size: int

    def __init__(self, length: bytes, flags: int, identifier: bytes):
        self.length = int.from_bytes(length, byteorder='big', signed=False)
        self.flags = flags
        self.identifier = int.from_bytes(identifier, byteorder='big', signed=False)
        ...

    def set_payload(self, chunk: bytes):
        value = chunk[:self.payload_size]
        self.make_payload(value)
        return chunk[self.payload_size:]

    def make_payload(self, value: bytes):
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

    def make_payload(self, value: bytes):
        payload = SettingPayload(
            identifier=value[:2],
            value=value[2:]
        )
        self.payload = payload


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

      Reserved (1),
      Stream Identifier (31),

      [Pad Length (8)],
      [Exclusive (1)],
      [Stream Dependency (31)],
      [Weight (8)],
      Field Block Fragment (..),
      Padding (..2040),
    }
    """
    type = 0x01


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
    type = 0x04


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


