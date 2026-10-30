from collections.abc import AsyncIterator

from shop.application.port.outbound.market_feed import MarketFeed
from shop.application.port.outbound.product_repository import ProductRepository
from shop.application.use_case.catalog import require_product
from shop.domain.market.tick import Tick


class FollowProduct:
    def __init__(self, products: ProductRepository, market: MarketFeed) -> None:
        self._products = products
        self._market = market

    async def handle(self, sku: str) -> AsyncIterator[Tick]:
        return self._market.ticks(await require_product(self._products, sku))
