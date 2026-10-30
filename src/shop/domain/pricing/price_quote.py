from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PriceQuote:
    tax_rate: Decimal
    discount_rate: Decimal
