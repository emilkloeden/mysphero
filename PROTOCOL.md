# Sphero V2 Protocol Reference

This document explains the binary protocol used by the Sphero Bolt+ (and other V2 Sphero devices). It's written for developers who are comfortable with software but new to working with raw bytes over Bluetooth.

## Big picture

Your phone (or laptop) talks to the Sphero over Bluetooth Low Energy (BLE). BLE works like a database of small values called **characteristics**, each identified by a UUID. You write bytes to a characteristic to send a command, and you receive bytes back via **notifications** on the same characteristic.

The Sphero Bolt+ exposes one characteristic that matters:

| UUID | Purpose |
|------|---------|
| `00010002-574f-4f20-5370-6865726f2121` | All commands AND responses (bidirectional) |

That's it. You write command packets here and subscribe to notifications here. There is no separate "TX" and "RX" — it's the same pipe in both directions.

## Packet structure

Every packet is a sequence of bytes wrapped between two marker bytes:

```
[SOP] [payload...] [CHK] [EOP]
  │                   │     │
  │                   │     └─ 0xD8 — End Of Packet
  │                   └─ checksum byte (see below)
  └─ 0x8D — Start Of Packet
```

The payload between SOP and EOP has this layout:

```
[FLAGS] [TID?] [SID?] [DID] [CID] [SEQ] [ERR?] [DATA...] [CHK]
```

### Field by field

| Field | Size | Description |
|-------|------|-------------|
| **FLAGS** | 1 byte | Bitfield that controls packet behaviour (see below) |
| **TID** | 0 or 1 byte | Target processor ID. Only present if FLAGS bit 4 is set |
| **SID** | 0 or 1 byte | Source ID (who sent this). Only present if FLAGS bit 5 is set |
| **DID** | 1 byte | Device ID — which subsystem on the Sphero you're talking to |
| **CID** | 1 byte | Command ID — which operation within that subsystem |
| **SEQ** | 1 byte | Sequence number (0–254). You increment this with each command so you can match responses to requests |
| **ERR** | 0 or 1 byte | Error/status code. Only present in **responses** (FLAGS bit 0 set). `0x00` = success |
| **DATA** | 0+ bytes | Command-specific payload |
| **CHK** | 1 byte | Checksum of everything before it (FLAGS through DATA) |

### Flags

```
Bit 0 (0x01)  is_response        — Set in packets FROM the device
Bit 1 (0x02)  requests_response  — Ask the device to reply
Bit 2 (0x04)  requests_error_only — Only reply if there's an error
Bit 3 (0x08)  is_activity        — Resets the device's inactivity/sleep timer
Bit 4 (0x10)  has_target_id      — TID field is present
Bit 5 (0x20)  has_source_id      — SID field is present
```

For outgoing commands we use `0x0A` (request response + activity) as the base, plus `0x10` and `0x20` if we include TID/SID. That gives us `0x3A` for a typical routed command.

### Target and Source IDs

The Sphero Bolt+ has one processor (the "primary", TID `0x11`). The regular Bolt has a second processor (`0x12`) that runs its 8x8 LED matrix — the Bolt+ does not have this.

SID is always `0x01` (meaning "the API client", i.e. you).

TID/SID are optional. Commands without them still work — the device routes to the primary processor by default. But including them is good practice and matches what the official apps do.

### Checksum

```
checksum = 0xFF - (sum_of_all_payload_bytes & 0xFF)
```

"All payload bytes" means everything between (but not including) SOP and EOP, excluding the checksum byte itself. So: FLAGS + [TID] + [SID] + DID + CID + SEQ + [ERR] + DATA.

This is a simple sum-then-complement. If your bytes add up to 0x01A3, you take `0xA3`, then `0xFF - 0xA3 = 0x5C`. The receiver does the same sum (including the checksum byte) and checks that the low byte is `0xFF`.

### Escape sequences

The bytes `0x8D` (SOP), `0xD8` (EOP), and `0xAB` (the escape marker itself) can't appear literally inside the payload. If your data happens to contain one of these, it gets escaped:

| Raw byte | Sent as | How it works |
|----------|---------|--------------|
| `0x8D` | `0xAB 0x05` | Clear the top bit of 0x88 mask: `0x8D & ~0x88 = 0x05` |
| `0xD8` | `0xAB 0x50` | `0xD8 & ~0x88 = 0x50` |
| `0xAB` | `0xAB 0x23` | `0xAB & ~0x88 = 0x23` |

To unescape: when you see `0xAB`, take the next byte and OR it with `0x88`.

The checksum is calculated on the **unescaped** bytes. You compute the checksum first, then escape everything (including the checksum byte) before wrapping with SOP/EOP.

### Worked example

Let's set the front and back LEDs to red (255, 0, 0).

**Step 1: Assemble the unescaped payload**

```
FLAGS = 0x3A       (response + activity + has_tid + has_sid)
TID   = 0x11       (primary processor)
SID   = 0x01       (us, the API client)
DID   = 0x1A       (User IO subsystem)
CID   = 0x1C       (set_all_leds_with_8_bit_mask)
SEQ   = 0x00       (first command)
DATA  = 3F FF 00 00 FF 00 00
         │  └──────┘  └──────┘
         │  front RGB  back RGB
         └─ mask: all 6 LED channels (0x3F = bits 0–5)
```

Payload bytes: `3A 11 01 1A 1C 00 3F FF 00 00 FF 00 00`

**Step 2: Compute checksum**

```
sum = 0x3A + 0x11 + 0x01 + 0x1A + 0x1C + 0x00 + 0x3F + 0xFF + 0x00 + 0x00 + 0xFF + 0x00 + 0x00
    = 0x1BF
checksum = 0xFF - (0x1BF & 0xFF) = 0xFF - 0xBF = 0x40
```

**Step 3: Escape and wrap**

None of these bytes are 0x8D, 0xD8, or 0xAB, so no escaping needed.

Final packet: `8D 3A 11 01 1A 1C 00 3F FF 00 00 FF 00 00 40 D8`

**Step 4: Device responds**

```
8D 39 11 01 1A 1C 00 00 7E D8
   │  │   │  │   │  │  │  └─ EOP
   │  │   │  │   │  │  └─ checksum
   │  │   │  │   │  └─ ERR = 0x00 (success!)
   │  │   │  │   └─ SEQ = 0x00 (matches our request)
   │  │   │  └─ CID = 0x1C
   │  │   └─ DID = 0x1A
   │  └─ TID=0x11, SID=0x01
   └─ FLAGS = 0x39 (is_response + is_activity + has_tid + has_source_id)
```

## Known commands for the Bolt+

All tested and confirmed on real hardware. The Device ID for all LED/IO commands is **0x1A** (User IO).

### Set front + back LEDs (CID 0x1C)

Sets the individual LED colour channels. The first data byte is a bitmask selecting which channels to set, followed by RGB values for each selected group.

```
DID  = 0x1A
CID  = 0x1C
TID  = 0x11 (primary processor)
DATA = [mask] [rgb...]
```

**LED bitmask:**

| Bit | Mask | Channel |
|-----|------|---------|
| 0 | 0x01 | Front red |
| 1 | 0x02 | Front green |
| 2 | 0x04 | Front blue |
| 3 | 0x08 | Back red |
| 4 | 0x10 | Back green |
| 5 | 0x20 | Back blue |

Common masks:
- `0x07` — front LED only (3 bytes of RGB follow)
- `0x38` — back LED only (3 bytes of RGB follow)
- `0x3F` — both front and back (6 bytes: front RGB then back RGB)

**Example — front green, back blue:**
```
DATA = [0x3F, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF]
              └─ front ──────┘  └── back ────────┘
```

### Commands from the Bolt (untested on Bolt+)

These are documented in the `spherov2` library for the regular Bolt. They target the secondary processor (TID 0x12) which the Bolt+ responded to with error `0x09` (bad target). Listed here for reference:

| Command | CID | TID | Data | Notes |
|---------|-----|-----|------|-------|
| Matrix one colour | 0x2F | 0x12 | `[R, G, B]` | Fill entire 8x8 matrix |
| Matrix set pixel | 0x2D | 0x12 | `[x, y, R, G, B]` | Single pixel |
| Matrix text scroll | 0x3B | 0x12 | `[R, G, B, speed, repeat, ...chars, 0x00]` | Scrolling text |
| Matrix character | 0x42 | 0x12 | `[R, G, B, char]` | Single character |
| Matrix fill rect | 0x3E | 0x12 | `[x1, y1, x2, y2, R, G, B]` | Rectangle |
| Matrix line | 0x3D | 0x12 | `[x1, y1, x2, y2, R, G, B]` | Line |

## Bolt+ vs Bolt differences

| Feature | Bolt | Bolt+ |
|---------|------|-------|
| BLE name prefix | `SB-` | `BP-` |
| Primary processor (TID 0x11) | Yes | Yes |
| Secondary processor (TID 0x12) | Yes (LED matrix) | No (error 0x09) |
| Anti-DOS handshake characteristic | Yes (`00020005-...`) | Not present |
| 8x8 LED matrix | Yes | No |
| Front + back LEDs | Yes (CID 0x1C) | Yes (CID 0x1C) |

## Discovering more commands

The `spherov2` library is the best existing reference for the Sphero V2 protocol. There are several ways to map out additional Bolt+ capabilities:

### 1. Read the spherov2 source code

The library defines commands as Python methods with DID/CID metadata. The key files:

- **`spherov2/commands/io.py`** — LED and sensor I/O commands (DID 0x1A)
- **`spherov2/commands/drive.py`** — Motor and driving commands
- **`spherov2/commands/power.py`** — Battery, sleep, wake
- **`spherov2/commands/system_info.py`** — Firmware version, model number
- **`spherov2/toy/bolt.py`** — Which commands the Bolt uses and which processor they route to

Install it (`pip install spherov2`) and read the command definitions. Each method maps directly to a DID/CID pair.

### 2. Systematic probing

Write a script that sends commands from known DID/CID pairs and logs whether the response is success (`0x00`) or an error. You already have the debug script infrastructure for this. Good candidates to try first:

- **System Info (DID 0x11)** — `get_main_app_version` (CID 0x00), `get_board_revision` (CID 0x00 with different DID)
- **Power (DID 0x13)** — `get_battery_voltage` (CID 0x03), `get_battery_percentage` (CID 0x10)
- **Drive (DID 0x16)** — `set_raw_motors` (CID 0x01), `drive_with_heading` (CID 0x07)

### 3. BLE sniffing

If you have an Android phone, the **nRF Connect** app can log all BLE traffic between the official Sphero Edu app and the device. This shows you the exact packets the app sends for every feature. On desktop, Wireshark with a BLE sniffer dongle can do the same.

### 4. Response analysis

Every response includes an error code. The known codes:

| Code | Meaning |
|------|---------|
| 0x00 | Success |
| 0x01 | Bad device ID |
| 0x02 | Bad command ID |
| 0x03 | Not yet implemented |
| 0x04 | Restricted (command rejected) |
| 0x05 | Bad data length |
| 0x06 | Command failed |
| 0x07 | Bad parameter value |
| 0x08 | Busy |
| 0x09 | Bad target ID |
| 0x0A | Target unavailable |

These codes tell you exactly why a command failed, which makes systematic probing practical — you can distinguish "this command doesn't exist" from "I sent the wrong data".
