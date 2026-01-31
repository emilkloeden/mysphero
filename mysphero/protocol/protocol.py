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

    async def send(
        self, did: int, cid: int, data: bytes = b"",
        *, tid: int | None = None, sid: int | None = None,
    ):
        seq = self.seq
        self.seq = (self.seq + 1) % 255

        pkt = encode_packet(did, cid, seq, data, tid=tid, sid=sid)
        self.pending[seq] = (did, cid)

        log.info(f"Sending packet: {pkt.hex(' ').upper()}")
        await self.transport.write(pkt)

    def _on_receive(self, data: bytes):
        for payload in self.assembler.push(data):
            rsp = decode_response(payload)
            if rsp:
                seq = rsp["seq"]
                self.pending.pop(seq, None)
                log.debug(f"Response: SEQ={seq} code={rsp['code']}")
