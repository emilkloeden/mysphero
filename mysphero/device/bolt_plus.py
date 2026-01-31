from mysphero.protocol.protocol import Protocol
from mysphero.transport.transport import Transport


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
        await self.protocol.send(0x02, 0x20, bytes([r, g, b]))
