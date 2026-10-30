from pycraftcore.repository.port import AsyncRepository

from shop.domain.file.stored_file import StoredFile


class SqliteFileRepository:
    def __init__(self, repository: AsyncRepository) -> None:
        self._repository = repository

    async def save(self, file: StoredFile, content: bytes) -> None:
        await self._repository.execute(
            "INSERT OR REPLACE INTO files VALUES (?, ?, ?)", (file.name, file.size, content)
        )
