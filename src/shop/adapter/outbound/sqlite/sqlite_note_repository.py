from pycraftcore.repository.port import AsyncRepository

from shop.domain.note.note import Note


class SqliteNoteRepository:
    def __init__(self, repository: AsyncRepository) -> None:
        self._repository = repository

    async def save(self, note: Note) -> None:
        await self._repository.execute(
            "INSERT OR REPLACE INTO notes VALUES (?, ?, ?)", (note.digest, note.words, note.text)
        )
