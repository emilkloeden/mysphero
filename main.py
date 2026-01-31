from mysphero.transport.simulatedtransport import SimulatedTransport
from mysphero.device.bolt_plus import BoltPlus


def main():
    transport = SimulatedTransport(mtu=8)
    bolt = BoltPlus(transport)
    bolt.set_main_led((10, 20, 30))


if __name__ == "__main__":
    main()
