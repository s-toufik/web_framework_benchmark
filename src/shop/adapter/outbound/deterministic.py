import hashlib


def number(*parts: object) -> int:
    key = ":".join(str(part) for part in parts).encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8])


def token(*parts: object) -> str:
    key = ":".join(str(part) for part in parts).encode()
    return hashlib.sha256(key).hexdigest()[:12].upper()
