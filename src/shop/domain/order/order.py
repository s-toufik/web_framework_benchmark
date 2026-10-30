from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from shop.domain.exception.product_not_found import ProductNotFound
from shop.domain.order.order_request import OrderRequest
from shop.domain.pricing.money import to_cents
from shop.domain.pricing.price_quote import PriceQuote
from shop.domain.product.product import Product


@dataclass(frozen=True, slots=True)
class PricedLine:
    sku: str
    name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True, slots=True)
class Order:
    reference: str
    customer: str
    lines: tuple[PricedLine, ...]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal

    @classmethod
    def price(
        cls, request: OrderRequest, products: Mapping[str, Product], quote: PriceQuote
    ) -> Order:
        lines = tuple(_priced(line.sku, line.quantity, products) for line in request.lines)
        subtotal = to_cents(sum((line.line_total for line in lines), Decimal(0)))
        discount = to_cents(subtotal * quote.discount_rate)
        tax = to_cents((subtotal - discount) * quote.tax_rate)
        return cls(
            reference=request.reference,
            customer=request.customer,
            lines=lines,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=subtotal - discount + tax,
        )

    @property
    def items(self) -> int:
        return sum(line.quantity for line in self.lines)


def _priced(sku: str, quantity: int, products: Mapping[str, Product]) -> PricedLine:
    product = products.get(sku)
    if product is None:
        raise ProductNotFound(sku)
    return PricedLine(
        sku=sku,
        name=product.name,
        quantity=quantity,
        unit_price=product.price,
        line_total=to_cents(product.price * quantity),
    )
