from collections.abc import AsyncIterator, Mapping

from shop.application.port.outbound.inventory_api import InventoryApi
from shop.application.port.outbound.order_repository import OrderRepository
from shop.application.port.outbound.pricing_api import PricingApi
from shop.application.port.outbound.product_repository import ProductRepository
from shop.domain.exception.product_not_found import ProductNotFound
from shop.domain.order.order import Order
from shop.domain.order.order_request import OrderRequest
from shop.domain.order.tracking_event import TrackingEvent, TrackingStage
from shop.domain.product.product import Product


class TrackOrder:
    def __init__(
        self,
        products: ProductRepository,
        pricing: PricingApi,
        inventory: InventoryApi,
        orders: OrderRepository,
    ) -> None:
        self._products = products
        self._pricing = pricing
        self._inventory = inventory
        self._orders = orders

    async def handle(self, request: OrderRequest) -> AsyncIterator[TrackingEvent]:
        found = {product.sku: product for product in await self._products.products(request.skus)}
        missing = [sku for sku in request.skus if sku not in found]
        if missing:
            raise ProductNotFound(missing[0])
        return self._stages(request, found)

    async def _stages(
        self, request: OrderRequest, found: Mapping[str, Product]
    ) -> AsyncIterator[TrackingEvent]:
        reference = request.reference
        yield TrackingEvent(TrackingStage.RECEIVED, reference, f"{len(request.lines)} lines")
        yield TrackingEvent(TrackingStage.VALIDATED, reference, f"{len(found)} products found")
        quote = await self._pricing.quote(request.customer, request.lines)
        order = Order.price(request, found, quote)
        yield TrackingEvent(TrackingStage.PRICED, reference, f"total {order.total} EUR")
        reservation = await self._inventory.reserve(reference, request.lines)
        yield TrackingEvent(TrackingStage.RESERVED, reference, f"reservation {reservation}")
        await self._orders.save(order)
        yield TrackingEvent(TrackingStage.CONFIRMED, reference, f"{order.items} items confirmed")
