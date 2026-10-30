from shop.application.port.outbound.order_repository import OrderRepository
from shop.application.port.outbound.pricing_api import PricingApi
from shop.application.port.outbound.product_repository import ProductRepository
from shop.domain.order.order import Order
from shop.domain.order.order_request import OrderRequest


class PlaceOrder:
    def __init__(
        self, products: ProductRepository, pricing: PricingApi, orders: OrderRepository
    ) -> None:
        self._products = products
        self._pricing = pricing
        self._orders = orders

    async def handle(self, request: OrderRequest) -> Order:
        found = {product.sku: product for product in await self._products.products(request.skus)}
        quote = await self._pricing.quote(request.customer, request.lines)
        order = Order.price(request, found, quote)
        await self._orders.save(order)
        return order
