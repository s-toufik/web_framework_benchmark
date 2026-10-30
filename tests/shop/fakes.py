from collections.abc import AsyncIterator, Sequence
from decimal import Decimal

from shop.domain.market.tick import Tick
from shop.domain.order.order_line import OrderLine
from shop.domain.pricing.price_quote import PriceQuote
from shop.domain.product.product import Product
from shop.domain.product.stock import Stock

KETTLE = Product("SKU-00001", "Smart Kettle", "kitchen", Decimal("49.90"), 1200)
MUG = Product("SKU-00002", "Classic Mug", "kitchen", Decimal("9.99"), 350)
QUOTE = PriceQuote(tax_rate=Decimal("0.20"), discount_rate=Decimal("0.05"))


class InMemoryProducts:
    def __init__(self, *products: Product) -> None:
        self._products = {product.sku: product for product in products}

    async def product(self, sku: str) -> Product | None:
        return self._products.get(sku)

    async def products(self, skus: Sequence[str]) -> list[Product]:
        return [self._products[sku] for sku in skus if sku in self._products]

    async def image(self, sku: str) -> bytes | None:
        return f"image of {sku}".encode() if sku in self._products else None


class RecordingStore:
    def __init__(self) -> None:
        self.saved: list[object] = []

    async def save(self, *items: object) -> None:
        self.saved.append(items[0])


class FixedInventory:
    async def stock(self, sku: str) -> Stock:
        return Stock(sku, 7, "Lyon")

    async def reserve(self, reference: str, lines: Sequence[OrderLine]) -> str:
        return f"RSV-{reference}"


class FixedPricing:
    async def quote(self, customer: str, lines: Sequence[OrderLine]) -> PriceQuote:
        return QUOTE


class FixedMarket:
    async def ticks(self, product: Product) -> AsyncIterator[Tick]:
        for sequence in (1, 2):
            yield Tick(product.sku, sequence, product.price, sequence)
