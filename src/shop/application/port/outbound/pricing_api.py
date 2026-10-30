from collections.abc import Sequence
from typing import Protocol

from shop.domain.order.order_line import OrderLine
from shop.domain.pricing.price_quote import PriceQuote


class PricingApi(Protocol):
    async def quote(self, customer: str, lines: Sequence[OrderLine]) -> PriceQuote: ...
