from dataclasses import dataclass
from enum import StrEnum


class TrackingStage(StrEnum):
    RECEIVED = "received"
    VALIDATED = "validated"
    PRICED = "priced"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"


@dataclass(frozen=True, slots=True)
class TrackingEvent:
    stage: TrackingStage
    reference: str
    detail: str
