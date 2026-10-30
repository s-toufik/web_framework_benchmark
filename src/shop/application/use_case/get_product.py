import asyncio

from shop.application.port.outbound.inventory_api import InventoryApi
from shop.application.port.outbound.pricing_api import PricingApi
from shop.application.port.outbound.product_repository import ProductRepository
from shop.application.use_case.catalog import require_product
from shop.domain.order.order_line import OrderLine
from shop.domain.product.product_offer import ProductOffer


class GetProduct:
    def __init__(
        self, products: ProductRepository, inventory: InventoryApi, pricing: PricingApi
    ) -> None:
        self._products = products
        self._inventory = inventory
        self._pricing = pricing

    async def handle(self, sku: str) -> ProductOffer:
        product = await require_product(self._products, sku)
        stock, quote = await asyncio.gather(
            self._inventory.stock(sku),
            self._pricing.quote("catalog", (OrderLine(sku, 1),)),
        )
        return ProductOffer.of(product, stock, quote)
