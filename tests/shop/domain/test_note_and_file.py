import hashlib

from shop.domain.file.stored_file import StoredFile
from shop.domain.note.note import Note


def test_a_note_is_normalised_and_counted() -> None:
    note = Note.of("  The cat   saw the dog.\n\n\nThe end  \n")

    assert note.text == "The cat saw the dog.\nThe end"
    assert (note.lines, note.words, note.characters) == (2, 7, len(note.text))
    assert note.top_words[0] == ("the", 3)
    assert note.summary.startswith(f"note {note.digest}\n")


def test_a_stored_file_is_named_after_its_sha256() -> None:
    stored = StoredFile.of(b"payload")

    assert stored.digest == hashlib.sha256(b"payload").digest()
    assert (stored.name, stored.size) == (hashlib.sha256(b"payload").hexdigest(), 7)
