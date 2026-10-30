import asyncio
from collections.abc import Sequence
from decimal import Decimal
from typing import Final

from shop.adapter.outbound.deterministic import number
from shop.domain.order.order_line import OrderLine
from shop.domain.pricing.price_quote import PriceQuote

TAX_RATE: Final[Decimal] = Decimal("0.20")
LOYAL_CUSTOMER_DISCOUNT: Final[Decimal] = Decimal("0.02")
VOLUME_DISCOUNTS: Final[tuple[tuple[int, Decimal], ...]] = (
    (25, Decimal("0.10")),
    (10, Decimal("0.05")),
)


class FakePricingApi:
    def __init__(self, latency_seconds: float) -> None:
        self._latency = latency_seconds

    async def quote(self, customer: str, lines: Sequence[OrderLine]) -> PriceQuote:
        await asyncio.sleep(self._latency)
        items = sum(line.quantity for line in lines)
        volume = next((rate for minimum, rate in VOLUME_DISCOUNTS if items >= minimum), Decimal(0))
        loyalty = LOYAL_CUSTOMER_DISCOUNT if number("tier", customer) % 4 == 0 else Decimal(0)
        return PriceQuote(tax_rate=TAX_RATE, discount_rate=volume + loyalty)
