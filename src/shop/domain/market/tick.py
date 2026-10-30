from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Tick:
    sku: str
    sequence: int
    price: Decimal
    available: int
