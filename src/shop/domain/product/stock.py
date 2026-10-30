from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Stock:
    sku: str
    available: int
    warehouse: str
