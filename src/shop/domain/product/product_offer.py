from dataclasses import dataclass
from decimal import Decimal

from shop.domain.pricing.money import to_cents
from shop.domain.pricing.price_quote import PriceQuote
from shop.domain.product.product import Product
from shop.domain.product.stock import Stock


@dataclass(frozen=True, slots=True)
class ProductOffer:
    product: Product
    stock: Stock
    price_with_tax: Decimal

    @classmethod
    def of(cls, product: Product, stock: Stock, quote: PriceQuote) -> ProductOffer:
        return cls(product, stock, to_cents(product.price * (1 + quote.tax_rate)))

    @property
    def in_stock(self) -> bool:
        return self.stock.available > 0
