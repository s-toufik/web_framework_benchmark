from typing import Protocol

from shop.domain.note.note import Note


class SaveNotePort(Protocol):
    async def handle(self, text: str) -> Note: ...
