from mysphero.device.util import make_response
from mysphero.packet.assembler import PacketAssembler
from mysphero.packet.util import checksum
from mysphero.logger.logger import log


class SimulatedSphero:
    def __init__(self):
        self.assembler = PacketAssembler()

        self.led = (0, 0, 0)  # RGB

    def receive(self, data: bytes) -> list[bytes]:
        responses = []

        for raw in self.assembler.push(data):
            rsp = self._handle_packet(raw)
            if rsp:
                responses.append(rsp)

        return responses

    def _handle_packet(self, raw: bytes) -> bytes | None:
        body = raw[2:-1]
        if checksum(body) != raw[-1]:
            return None

        flags, did, cid, seq, dlen = body[:5]
        payload = body[5:]

        # LED command
        log.debug(f"[SIM] Received RAW: {raw.hex(' ').upper()}")
        log.debug(f"""[SIM] Received TRANSLATED: 
                  flags= {flags:02X},
                  did= {did:02X},
                  cid= {cid:02X},
                  seq= {seq:02X},
                  dlen= {dlen},
                  payload= {payload.hex(" ").upper()},
                  """)
        if did == 0x02 and cid == 0x20 and len(payload) == 3:
            r, g, b = payload
            self.led = (r, g, b)
            print(f"[SIM] LED set to {self.led}")

            return make_response(did, cid, seq, code=0x00)

        # Default: success for unknown commands
        return make_response(did, cid, seq, code=0x00)
