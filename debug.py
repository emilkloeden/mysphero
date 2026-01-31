"""
Diagnostic script: tries multiple packet formats with different LED colours
to determine what the Sphero Bolt+ actually accepts.

Key fixes from spherov2 library research:
  - TX and RX use the SAME characteristic (00010002), not separate ones
  - EOP 0xD8 escapes to 0xAB 0x50 (mask is & ~0x88), not 0xAB 0x06
  - Flags for TID+SID commands: 0x3A (response|activity|has_tid|has_sid)
  - TID=0x11 for primary processor (front/back LEDs)
  - TID=0x12 for secondary processor (LED matrix)
  - Front/back LEDs: DID=0x1A, CID=0x1C, data=[mask, r,g,b, r,g,b]
  - Matrix single colour: DID=0x1A, CID=0x2F, data=[r,g,b]
  - No anti-DOS characteristic on Bolt+ (only exists on Bolt)
"""

import asyncio
from bleak import BleakClient
from mysphero.discovery.discovery import discover

# Bolt+ uses a single characteristic for both TX and RX
SPHERO_CHAR = "00010002-574f-4f20-5370-6865726f2121"


# ── packet builders ─────────────────────────────────────────────

def checksum(payload: bytes) -> int:
    return 0xFF - (sum(payload) & 0xFF)


def escape(data: bytes) -> bytes:
    """Escape bytes that collide with SOP/EOP/ESC markers.
    Mask is & ~0x88:  0x8D->0x05, 0xD8->0x50, 0xAB->0x23"""
    out = bytearray()
    for b in data:
        if b in (0x8D, 0xD8, 0xAB):
            out.append(0xAB)
            out.append(b & ~0x88)
        else:
            out.append(b)
    return bytes(out)


def build_v2(did, cid, seq, data, *, tid=None, sid=None):
    """Sphero V2 packet: [SOP 0x8D] [escaped payload+chk] [EOP 0xD8]"""
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
    return bytes([0x8D]) + escape(bytes(payload)) + bytes([0xD8])


# ── notification logger ─────────────────────────────────────────

def on_notify(sender, data: bytes):
    print(f"  << RX: {data.hex(' ').upper()}")


# ── main ────────────────────────────────────────────────────────

async def main():
    print("Scanning for Bolt+...")
    address = await discover("BP-", timeout=10.0)
    print(f"Found: {address}\n")

    client = BleakClient(address)
    await client.connect()
    print("BLE connected.")

    # subscribe to notifications on the SAME characteristic we write to
    await client.start_notify(SPHERO_CHAR, on_notify)
    print(f"Subscribed to notifications on {SPHERO_CHAR}\n")

    await asyncio.sleep(0.5)

    seq = 0
    tests = [
        # 1) RED - front+back LEDs via primary processor (TID=0x11)
        #    DID=0x1A CID=0x1C, mask=0x3F, front=red back=red
        ("RED     | front+back LEDs, TID=0x11, CID=0x1C mask=0x3F",
         build_v2(0x1A, 0x1C, seq,
                  bytes([0x3F, 255, 0, 0, 255, 0, 0]),
                  tid=0x11, sid=0x01)),

        # 2) GREEN - matrix single colour via secondary processor (TID=0x12)
        #    DID=0x1A CID=0x2F, data=[0,255,0]
        ("GREEN   | matrix one-colour, TID=0x12, CID=0x2F",
         build_v2(0x1A, 0x2F, (seq := seq + 1),
                  bytes([0, 255, 0]),
                  tid=0x12, sid=0x01)),

        # 3) BLUE - front LEDs only (mask=0x07), TID=0x11
        ("BLUE    | front LEDs only, TID=0x11, CID=0x1C mask=0x07",
         build_v2(0x1A, 0x1C, (seq := seq + 1),
                  bytes([0x07, 0, 0, 255]),
                  tid=0x11, sid=0x01)),

        # 4) YELLOW - same as test 1 but without TID/SID (plain V2)
        ("YELLOW  | no TID/SID, CID=0x1C mask=0x3F",
         build_v2(0x1A, 0x1C, (seq := seq + 1),
                  bytes([0x3F, 255, 255, 0, 255, 255, 0]))),

        # 5) CYAN - matrix one-colour without TID/SID
        ("CYAN    | no TID/SID, CID=0x2F",
         build_v2(0x1A, 0x2F, (seq := seq + 1),
                  bytes([0, 255, 255]))),

        # 6) WHITE - front+back via TID=0x12 (secondary) instead of 0x11
        #    in case Bolt+ routes differently than Bolt
        ("WHITE   | front+back LEDs, TID=0x12, CID=0x1C mask=0x3F",
         build_v2(0x1A, 0x1C, (seq := seq + 1),
                  bytes([0x3F, 255, 255, 255, 255, 255, 255]),
                  tid=0x12, sid=0x01)),
    ]

    PAUSE = 3

    for i, (label, pkt) in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {label}")
        print(f"  >> TX: {pkt.hex(' ').upper()}")
        await client.write_gatt_char(SPHERO_CHAR, pkt, response=False)
        await asyncio.sleep(PAUSE)
        print()

    print("All tests sent. Holding connection 5s before disconnect...")
    await asyncio.sleep(5)
    await client.disconnect()
    print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
