import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredFile:
    digest: bytes
    size: int

    @classmethod
    def of(cls, content: bytes) -> StoredFile:
        return cls(hashlib.sha256(content).digest(), len(content))

    @property
    def name(self) -> str:
        return self.digest.hex()
