from mysphero.packet.util import encode_packet


def make_response(did, cid, seq, code=0x00, data=b""):
    # Build a response packet: flags will have is_response (0x01) set
    # We encode it as a regular packet then patch the flags byte
    # Simpler: just build the raw response directly
    from mysphero.packet.constants import SOP, EOP
    from mysphero.packet.util import checksum, escape

    flags = 0x09  # is_response | is_activity
    payload = bytearray([flags, did, cid, seq, code])
    payload.extend(data)
    payload.append(checksum(payload))
    return bytes([SOP]) + escape(bytes(payload)) + bytes([EOP])
