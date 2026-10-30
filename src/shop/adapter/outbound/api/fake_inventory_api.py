import asyncio
from collections.abc import Sequence
from typing import Final

from shop.adapter.outbound.deterministic import number, token
from shop.domain.order.order_line import OrderLine
from shop.domain.product.stock import Stock

WAREHOUSES: Final[tuple[str, ...]] = ("Lyon", "Lille", "Nantes", "Toulouse")


class FakeInventoryApi:
    def __init__(self, latency_seconds: float) -> None:
        self._latency = latency_seconds

    async def stock(self, sku: str) -> Stock:
        await asyncio.sleep(self._latency)
        value = number("stock", sku)
        return Stock(sku=sku, available=value % 500, warehouse=WAREHOUSES[value % len(WAREHOUSES)])

    async def reserve(self, reference: str, lines: Sequence[OrderLine]) -> str:
        await asyncio.sleep(self._latency)
        return "RSV-" + token(reference, *(f"{line.sku}x{line.quantity}" for line in lines))
