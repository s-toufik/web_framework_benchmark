from collections.abc import Sequence
from typing import Protocol

from shop.domain.order.order_line import OrderLine
from shop.domain.product.stock import Stock


class InventoryApi(Protocol):
    async def stock(self, sku: str) -> Stock: ...

    async def reserve(self, reference: str, lines: Sequence[OrderLine]) -> str: ...
