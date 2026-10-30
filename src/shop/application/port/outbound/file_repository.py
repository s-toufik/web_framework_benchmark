from typing import Protocol

from shop.domain.file.stored_file import StoredFile


class FileRepository(Protocol):
    async def save(self, file: StoredFile, content: bytes) -> None: ...
