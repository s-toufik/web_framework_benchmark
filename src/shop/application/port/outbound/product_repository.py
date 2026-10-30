from collections.abc import Sequence
from typing import Protocol

from shop.domain.product.product import Product


class ProductRepository(Protocol):
    async def product(self, sku: str) -> Product | None: ...

    async def products(self, skus: Sequence[str]) -> list[Product]: ...

    async def image(self, sku: str) -> bytes | None: ...
