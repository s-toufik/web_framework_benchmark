import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal

from shop.adapter.outbound.deterministic import number
from shop.domain.market.tick import Tick
from shop.domain.pricing.money import to_cents
from shop.domain.product.product import Product


class FakeMarketFeed:
    def __init__(self, interval_seconds: float, ticks: int) -> None:
        self._interval = interval_seconds
        self._ticks = ticks

    async def ticks(self, product: Product) -> AsyncIterator[Tick]:
        for sequence in range(1, self._ticks + 1):
            await asyncio.sleep(self._interval)
            value = number("tick", product.sku, sequence)
            change = Decimal(value % 401 - 200) / 10_000
            yield Tick(
                sku=product.sku,
                sequence=sequence,
                price=to_cents(product.price * (1 + change)),
                available=value % 300,
            )
