class Transport:
    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def set_receive_callback(self, fn) -> None:
        raise NotImplementedError
