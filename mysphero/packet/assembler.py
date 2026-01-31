from mysphero.packet.constants import SOP1, SOP2


class PacketAssembler:
    def __init__(self):
        self.buffer = bytearray()

    def push(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        packets = []

        while True:
            if len(self.buffer) < 7:
                break

            if self.buffer[0] != SOP1 or self.buffer[1] != SOP2:
                del self.buffer[0]
                continue

            dlen = self.buffer[6]
            total_len = 7 + dlen

            if len(self.buffer) < total_len:
                break

            pkt = bytes(self.buffer[:total_len])
            del self.buffer[:total_len]
            packets.append(pkt)

        return packets
