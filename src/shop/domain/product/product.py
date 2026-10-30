from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Product:
    sku: str
    name: str
    category: str
    price: Decimal
    weight_grams: int
