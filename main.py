from mysphero.transport.simulatedtransport import SimulatedTransport
from mysphero.protocol.protocol import Protocol


def main():
    transport = SimulatedTransport(mtu=8)
    proto = Protocol(transport)

    data = bytes([10, 20, 30])
    proto.send(0x02, 0x20, data)


if __name__ == "__main__":
    main()
