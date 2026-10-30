from shop.application.port.outbound.product_repository import ProductRepository
from shop.domain.exception.product_not_found import ProductNotFound
from shop.domain.product.product import Product


async def require_product(products: ProductRepository, sku: str) -> Product:
    product = await products.product(sku)
    if product is None:
        raise ProductNotFound(sku)
    return product
