from bleak import BleakScanner


async def discover(name: str, timeout: float = 5.0) -> str:
    devices = await BleakScanner.discover(timeout=timeout)
    for d in devices:
        if d.name and name in d.name:
            return d.address
    raise RuntimeError(f"Device matching '{name}' not found")
