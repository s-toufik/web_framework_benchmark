from dataclasses import dataclass
from enum import StrEnum


class EndpointKind(StrEnum):
    JSON = "json"
    STREAM = "stream"
    BINARY = "binary"
    TEXT = "text"


@dataclass(frozen=True, slots=True)
class Endpoint:
    name: str
    kind: EndpointKind
    method: str
    path: str
    media_type: str
    body: bytes | None = None
    content_type: str | None = None

    @property
    def label(self) -> str:
        return f"{self.method} {self.kind.value}"
