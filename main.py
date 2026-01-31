import asyncio
from mysphero.transport.simulatedtransport import SimulatedTransport
from mysphero.device.bolt_plus import BoltPlus


async def main():
    transport = SimulatedTransport(mtu=8)
    async with BoltPlus(transport) as bolt:
        await bolt.set_main_led((10, 20, 30))


if __name__ == "__main__":
    asyncio.run(main())
