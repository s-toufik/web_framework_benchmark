from typing import Protocol

from shop.domain.order.order import Order
from shop.domain.order.order_request import OrderRequest


class PlaceOrderPort(Protocol):
    async def handle(self, request: OrderRequest) -> Order: ...
