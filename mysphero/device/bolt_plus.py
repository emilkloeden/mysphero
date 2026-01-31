from mysphero.protocol.protocol import Protocol
from mysphero.transport.transport import Transport

DID_USER_IO = 0x1A
CID_SET_ALL_LEDS = 0x1C
TID_PRIMARY = 0x11
SID_CLIENT = 0x01
LED_MASK_FRONT_BACK = 0x3F


class BoltPlus:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.protocol = Protocol(transport)

    async def __aenter__(self):
        await self.transport.connect()
        return self

    async def __aexit__(self, *exc):
        await self.transport.disconnect()

    async def set_main_led(self, color: tuple[int, int, int]):
        r, g, b = color
        await self.protocol.send(
            DID_USER_IO, CID_SET_ALL_LEDS,
            bytes([LED_MASK_FRONT_BACK, r, g, b, r, g, b]),
            tid=TID_PRIMARY, sid=SID_CLIENT,
        )
