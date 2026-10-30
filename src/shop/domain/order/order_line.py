from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderLine:
    sku: str
    quantity: int
