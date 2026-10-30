from collections.abc import AsyncIterator
from typing import Protocol

from shop.domain.order.order_request import OrderRequest
from shop.domain.order.tracking_event import TrackingEvent


class TrackOrderPort(Protocol):
    async def handle(self, request: OrderRequest) -> AsyncIterator[TrackingEvent]: ...
