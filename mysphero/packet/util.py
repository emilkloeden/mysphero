from mysphero.packet.constants import SOP, EOP, ESC, ESC_MASK


def checksum(payload: bytes) -> int:
    return 0xFF - (sum(payload) & 0xFF)


def escape(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b in (SOP, EOP, ESC):
            out.append(ESC)
            out.append(b & ~ESC_MASK)
        else:
            out.append(b)
    return bytes(out)


def unescape(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        if data[i] == ESC and i + 1 < len(data):
            out.append(data[i + 1] | ESC_MASK)
            i += 2
        else:
            out.append(data[i])
            i += 1
    return bytes(out)


def encode_packet(
    did: int, cid: int, seq: int, data: bytes = b"",
    *, tid: int | None = None, sid: int | None = None,
) -> bytes:
    flags = 0x0A  # requests_response | is_activity
    if tid is not None:
        flags |= 0x10  # has_target_id
    if sid is not None:
        flags |= 0x20  # has_source_id

    payload = bytearray([flags])
    if tid is not None:
        payload.append(tid)
    if sid is not None:
        payload.append(sid)
    payload.extend([did, cid, seq])
    payload.extend(data)
    payload.append(checksum(payload))

    return bytes([SOP]) + escape(bytes(payload)) + bytes([EOP])


def decode_response(raw: bytes) -> dict | None:
    if len(raw) < 6:
        return None

    # raw is already unescaped and stripped of SOP/EOP by the assembler
    flags = raw[0]
    pos = 1

    tid = None
    if flags & 0x10:
        tid = raw[pos]
        pos += 1
    sid = None
    if flags & 0x20:
        sid = raw[pos]
        pos += 1

    did = raw[pos]
    cid = raw[pos + 1]
    seq = raw[pos + 2]
    pos += 3

    # responses (flags & 0x01) have an error code byte
    code = None
    if flags & 0x01:
        code = raw[pos]
        pos += 1

    data = raw[pos:-1]  # last byte is checksum

    return {
        "flags": flags,
        "tid": tid,
        "sid": sid,
        "did": did,
        "cid": cid,
        "seq": seq,
        "code": code,
        "data": data,
    }
