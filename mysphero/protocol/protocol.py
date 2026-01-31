from mysphero.packet.assembler import PacketAssembler
from mysphero.packet.util import decode_response, encode_packet
from mysphero.transport.transport import Transport
from mysphero.logger.logger import log


class Protocol:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.assembler = PacketAssembler()
        self.seq = 0
        self.pending = {}

        transport.set_receive_callback(self._on_receive)

    def make_command(
        self, did: int, cid: int, data: bytes = b"", flags: int = 0x0A
    ) -> bytes:
        seq = self.seq
        self.seq = (self.seq + 1) & 0xFF

        pkt = encode_packet(flags, did, cid, seq, data)
        self.pending[seq] = (did, cid)

        return pkt

    def handle_response(self, rsp: dict):
        seq = rsp["seq"]
        self.pending.pop(seq, None)
        return rsp

    async def send(self, did: int, cid: int, data: bytes = b""):
        pkt = self.make_command(did, cid, data)
        log.info(f"Sending packet: {pkt.hex(' ').upper()} (length: {len(pkt)})")
        await self.transport.write(pkt)

    def _on_receive(self, data: bytes):
        for raw in self.assembler.push(data):
            rsp = decode_response(raw)
            if rsp:
                self.handle_response(rsp)
