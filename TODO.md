# TODO

## Done

- [x] Layered architecture (Transport → Protocol → Packet → Device)
- [x] Simulated transport with MTU fragmentation
- [x] Async migration (full call chain is async/await)
- [x] BLE discovery (`mysphero/discovery/`)
- [x] BleakTransport — real BLE communication via `bleak`
- [x] V2 protocol implementation (SOP/EOP framing, escaping, checksum)
- [x] `BoltPlus.set_main_led()` confirmed working on real hardware
- [x] Protocol documentation (`PROTOCOL.md`)

## Next steps

### Solidify the foundation

- [ ] **Await command responses** — `Protocol.send()` currently fires and forgets. It should return a future that resolves when the matching SEQ response arrives (or times out). This is needed before any command that reads data back (battery, sensors, firmware version).
- [ ] **Update CLAUDE.md** — Architecture section still describes the old V1 packet format. Update to reflect V2 and the current file layout.
- [ ] **Replace `main.py` with tests** — Unit-test the packet layer (encode, decode, escape, checksum, assembler) using pytest. The simulated transport makes this easy — no hardware needed.

### Expand the command set

- [ ] **System info commands** — Query firmware version, board revision, model number (DID 0x11). Low-risk, read-only, good for verifying response parsing works end-to-end.
- [ ] **Power commands** — Battery voltage, battery percentage, sleep/wake (DID 0x13). Useful and safe to probe.
- [ ] **Driving** — `drive_with_heading`, `set_raw_motors` (DID 0x16). Needs care — the bot will move.
- [ ] **Sensor streaming** — Accelerometer, gyroscope, ambient light. These use async notifications rather than request/response, so they'll exercise the notification pipeline.

### Improve the developer experience

- [ ] **Enumerate Bolt+ capabilities with a probe script** — Iterate over known DID/CID pairs from `spherov2`, send each to the device, and log which ones return success vs error code. Produces a compatibility map for the Bolt+.
- [ ] **Higher-level API** — Methods like `bolt.set_front_led(r, g, b)`, `bolt.set_back_led(r, g, b)`, `bolt.drive(speed, heading)` that hide DID/CID/mask details.
- [ ] **Connection robustness** — Retry logic, disconnection detection, reconnection. BLE connections drop.
