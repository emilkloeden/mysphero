def chunk_bytes(data: bytes, size: int):
    for i in range(0, len(data), size):
        yield data[i : i + size]
