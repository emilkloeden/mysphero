from bleak import BleakClient
from mysphero.transport.transport import Transport

SPHERO_CHAR = "00010002-574f-4f20-5370-6865726f2121"


class BleakTransport(Transport):
    def __init__(self, address: str):
        self.client = BleakClient(address)
        self.rx_cb = None

    async def connect(self):
        await self.client.connect()
        await self.client.start_notify(SPHERO_CHAR, self._on_notify)

    async def disconnect(self):
        await self.client.disconnect()

    def set_receive_callback(self, fn):
        self.rx_cb = fn

    async def write(self, data: bytes):
        await self.client.write_gatt_char(SPHERO_CHAR, data, response=False)

    def _on_notify(self, sender, data: bytes):
        if self.rx_cb:
            self.rx_cb(data)
