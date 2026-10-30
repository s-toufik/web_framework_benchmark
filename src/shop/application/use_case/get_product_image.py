from shop.application.port.outbound.product_repository import ProductRepository
from shop.domain.exception.product_not_found import ProductNotFound


class GetProductImage:
    def __init__(self, products: ProductRepository) -> None:
        self._products = products

    async def handle(self, sku: str) -> bytes:
        image = await self._products.image(sku)
        if image is None:
            raise ProductNotFound(sku)
        return image
