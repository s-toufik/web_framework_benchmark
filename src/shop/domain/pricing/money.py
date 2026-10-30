from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

CENT: Final[Decimal] = Decimal("0.01")


def to_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_EVEN)
