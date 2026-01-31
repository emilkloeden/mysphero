from mysphero.packet.constants import SOP, EOP
from mysphero.packet.util import unescape, checksum


class PacketAssembler:
    def __init__(self):
        self.buffer = bytearray()

    def push(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        packets = []

        while True:
            # find SOP
            try:
                start = self.buffer.index(SOP)
            except ValueError:
                self.buffer.clear()
                break

            # discard any junk before SOP
            if start > 0:
                del self.buffer[:start]

            # find EOP
            try:
                end = self.buffer.index(EOP, 1)
            except ValueError:
                break  # incomplete packet, wait for more data

            # extract and unescape the payload between SOP and EOP
            raw_body = bytes(self.buffer[1:end])
            del self.buffer[:end + 1]

            payload = unescape(raw_body)
            if len(payload) < 2:
                continue

            # verify checksum (last byte) against the rest
            body, chk = payload[:-1], payload[-1]
            if checksum(body) != chk:
                continue

            packets.append(payload)

        return packets
