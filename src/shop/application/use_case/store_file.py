from shop.application.port.outbound.file_repository import FileRepository
from shop.domain.file.stored_file import StoredFile


class StoreFile:
    def __init__(self, files: FileRepository) -> None:
        self._files = files

    async def handle(self, content: bytes) -> StoredFile:
        file = StoredFile.of(content)
        await self._files.save(file, content)
        return file
