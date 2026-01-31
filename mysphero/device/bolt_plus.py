from mysphero.protocol.protocol import Protocol
from mysphero.transport.transport import Transport


class BoltPlus:
    def __init__(self, transport: Transport):
        self.protocol = Protocol(transport)

    def set_main_led(self, color: tuple[int, int, int]):
        r, g, b = color
        self.protocol.send(0x02, 0x20, bytes([r, g, b]))
