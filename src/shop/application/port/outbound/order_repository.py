from typing import Protocol

from shop.domain.order.order import Order


class OrderRepository(Protocol):
    async def save(self, order: Order) -> None: ...
