from typing import Protocol

from shop.domain.file.stored_file import StoredFile


class StoreFilePort(Protocol):
    async def handle(self, content: bytes) -> StoredFile: ...
