import hashlib
import re
from collections import Counter
from dataclasses import dataclass

TOP_WORDS: int = 5
_WORD = re.compile(r"[a-z0-9']+")


@dataclass(frozen=True, slots=True)
class Note:
    digest: str
    text: str
    lines: int
    words: int
    characters: int
    top_words: tuple[tuple[str, int], ...]

    @classmethod
    def of(cls, raw: str) -> Note:
        lines = [" ".join(line.split()) for line in raw.strip().splitlines()]
        text = "\n".join(line for line in lines if line)
        words = _WORD.findall(text.lower())
        ranked = sorted(Counter(words).items(), key=lambda item: (-item[1], item[0]))
        return cls(
            digest=hashlib.sha256(text.encode()).hexdigest()[:16],
            text=text,
            lines=text.count("\n") + 1 if text else 0,
            words=len(words),
            characters=len(text),
            top_words=tuple(ranked[:TOP_WORDS]),
        )

    @property
    def summary(self) -> str:
        top = ", ".join(f"{word} ({count})" for word, count in self.top_words)
        return (
            f"note {self.digest}\n"
            f"lines {self.lines}\n"
            f"words {self.words}\n"
            f"characters {self.characters}\n"
            f"top words {top}\n"
        )
