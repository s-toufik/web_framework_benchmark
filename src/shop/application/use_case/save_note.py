from shop.application.port.outbound.note_repository import NoteRepository
from shop.domain.note.note import Note


class SaveNote:
    def __init__(self, notes: NoteRepository) -> None:
        self._notes = notes

    async def handle(self, text: str) -> Note:
        note = Note.of(text)
        await self._notes.save(note)
        return note
