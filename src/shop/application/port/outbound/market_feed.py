from collections.abc import AsyncIterator
from typing import Protocol

from shop.domain.market.tick import Tick
from shop.domain.product.product import Product


class MarketFeed(Protocol):
    def ticks(self, product: Product) -> AsyncIterator[Tick]: ...
