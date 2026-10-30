from pydantic import BaseModel

from shop.domain.product.product_offer import ProductOffer


class ProductSchema(BaseModel):
    sku: str
    name: str
    category: str
    price: str
    price_with_tax: str
    weight_grams: int
    available: int
    warehouse: str
    in_stock: bool

    @classmethod
    def of(cls, offer: ProductOffer) -> ProductSchema:
        product, stock = offer.product, offer.stock
        return cls(
            sku=product.sku,
            name=product.name,
            category=product.category,
            price=str(product.price),
            price_with_tax=str(offer.price_with_tax),
            weight_grams=product.weight_grams,
            available=stock.available,
            warehouse=stock.warehouse,
            in_stock=offer.in_stock,
        )
