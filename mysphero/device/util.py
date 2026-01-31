from mysphero.packet.constants import SOP1, SOP2
from mysphero.packet.util import checksum


def make_response(did, cid, seq, code=0x00, data=b""):
    flags = 0x08  # response
    body = (
        bytes(
            [
                flags,
                did,
                cid,
                seq,
                len(data) + 2,  # code + checksum
                code,
            ]
        )
        + data
    )

    return bytes([SOP1, SOP2]) + body + bytes([checksum(body)])
