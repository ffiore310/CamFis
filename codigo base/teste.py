def int_to_bytes(x: int, byteorder: str = 'big') -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, byteorder)