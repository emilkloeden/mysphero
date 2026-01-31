# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MySphero is a Python library for controlling a Sphero Bolt+ robotic ball. Currently uses a simulated transport layer; real BLE support (via `bleak`) is planned.

## Development Setup

- **Python 3.13+** required (pinned in `.python-version`)
- **Package manager:** `uv`
- **Setup:** `uv sync`
- **Run demo:** `uv run python main.py`
- No test framework yet — `main.py` serves as the current manual test

## Architecture

The project follows a layered protocol architecture where each layer has a single responsibility:

```
Protocol  →  Transport  →  Device
   ↑             ↑            |
   └── Packet ───┘            |
       (assembler + codec)    |
                              ↓
                         (response flows back up via callbacks)
```

**Transport** (`mysphero/transport/`) — Abstract `Transport` base class with `write()` and `set_receive_callback()`. `SimulatedTransport` implements BLE-like behavior including MTU-based packet fragmentation on both send and receive.

**Protocol** (`mysphero/protocol/`) — Builds command packets with auto-incrementing sequence numbers, sends them through transport, and reassembles fragmented responses via `PacketAssembler`. Tracks in-flight commands in a `pending` dict keyed by sequence number.

**Packet** (`mysphero/packet/`) — Handles the Sphero binary protocol format: `[SOP1][SOP2][FLAGS][DID][CID][SEQ][DLEN][DATA...][CHECKSUM]`. `encode_packet()` builds commands, `decode_response()` parses responses, `PacketAssembler` reconstructs complete packets from a byte stream. Checksum is XOR-based (`~sum(body) & 0xFF`).

**Device** (`mysphero/device/`) — `SimulatedSphero` responds to commands (currently only LED color: DID=0x02, CID=0x20 with 3-byte RGB payload). Used by `SimulatedTransport` for testing without hardware.

**Data flow:** `Protocol.send()` encodes a command → `Transport.write()` fragments it by MTU and delivers to device → device processes and responds → transport delivers response fragments back → `Protocol._on_receive()` reassembles via `PacketAssembler` and decodes.

## Planned Work (from TODO.md)

- Higher-level API (e.g. `bolt.set_main_led(Color)`)
- `BleakTransport` for real BLE communication
- Replace `main.py` with a proper test suite
