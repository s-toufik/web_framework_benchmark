from typing import Protocol

from shop.domain.product.product_offer import ProductOffer


class GetProductPort(Protocol):
    async def handle(self, sku: str) -> ProductOffer: ...
