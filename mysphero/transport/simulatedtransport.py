from mysphero.simulation.simulatedsphero import SimulatedSphero
from mysphero.transport.transport import Transport
from mysphero.transport.util import chunk_bytes
from mysphero.logger.logger import log


class SimulatedTransport(Transport):
    def __init__(self, mtu: int = 20):
        self.device = SimulatedSphero()
        self.rx_cb = None
        self.mtu = mtu

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    def set_receive_callback(self, fn):
        self.rx_cb = fn

    async def write(self, data: bytes):
        # simulate BLE write fragmentation
        log.debug(f"[SIM TRANSPORT] Write: data={data.hex(' ').upper()} {len(data)=}")
        for chunk in chunk_bytes(data, self.mtu):
            responses = self.device.receive(chunk)

            # simulate notify fragmentation on the way back
            for rsp in responses:
                for rsp_chunk in chunk_bytes(rsp, self.mtu):
                    if self.rx_cb:
                        self.rx_cb(rsp_chunk)
