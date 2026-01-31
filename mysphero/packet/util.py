from mysphero.packet.constants import SOP1, SOP2


def checksum(data: bytes) -> int:
    return ~sum(data) & 0xFF


def encode_packet(flags: int, did: int, cid: int, seq: int, data: bytes) -> bytes:
    dlen = len(data) + 1  # +1 for checksum

    body = (
        bytes(
            [
                flags,
                did,
                cid,
                seq,
                dlen,
            ]
        )
        + data
    )

    chk = checksum(body)

    return bytes([SOP1, SOP2]) + body + bytes([chk])


def decode_response(raw: bytes):
    if len(raw) < 9:
        return None

    body = raw[2:-1]
    chk = raw[-1]

    if checksum(body) != chk:
        return None

    return {
        "flags": body[0],
        "did": body[1],
        "cid": body[2],
        "seq": body[3],
        "code": body[5],
        "data": body[6:],
    }
