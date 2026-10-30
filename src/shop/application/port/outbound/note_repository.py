from typing import Protocol

from shop.domain.note.note import Note


class NoteRepository(Protocol):
    async def save(self, note: Note) -> None: ...
