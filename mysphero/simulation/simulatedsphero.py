from mysphero.simulation.util import make_response
from mysphero.packet.assembler import PacketAssembler
from mysphero.packet.util import decode_response
from mysphero.logger.logger import log


class SimulatedSphero:
    def __init__(self):
        self.assembler = PacketAssembler()
        self.led = (0, 0, 0)

    def receive(self, data: bytes) -> list[bytes]:
        responses = []

        for payload in self.assembler.push(data):
            rsp = self._handle_packet(payload)
            if rsp:
                responses.append(rsp)

        return responses

    def _handle_packet(self, payload: bytes) -> bytes | None:
        parsed = decode_response(payload)
        if parsed is None:
            return None

        did = parsed["did"]
        cid = parsed["cid"]
        seq = parsed["seq"]
        data = parsed["data"]

        log.debug(f"[SIM] Received: DID={did:#04x} CID={cid:#04x} SEQ={seq} data={data.hex(' ').upper()}")

        # LED command: DID=0x1A, CID=0x1C (set_all_leds_with_8_bit_mask)
        if did == 0x1A and cid == 0x1C and len(data) >= 4:
            mask = data[0]
            rgb_data = data[1:]
            if mask & 0x07 and len(rgb_data) >= 3:
                r, g, b = rgb_data[0], rgb_data[1], rgb_data[2]
                self.led = (r, g, b)
                print(f"[SIM] LED set to {self.led}")
            return make_response(did, cid, seq, code=0x00)

        return make_response(did, cid, seq, code=0x00)
