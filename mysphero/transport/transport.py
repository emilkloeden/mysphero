class Transport:
    async def connect(self) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def write(self, data: bytes) -> None:
        raise NotImplementedError

    def set_receive_callback(self, fn) -> None:
        raise NotImplementedError
