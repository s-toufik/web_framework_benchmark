from typing import Protocol

from shop.domain.product.label import Label


class RenderLabelPort(Protocol):
    async def handle(self, sku: str) -> Label: ...
