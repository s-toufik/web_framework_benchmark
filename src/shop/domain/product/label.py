from dataclasses import dataclass

from shop.domain.product.product_offer import ProductOffer

WIDTH: int = 40


@dataclass(frozen=True, slots=True)
class Label:
    text: str

    @classmethod
    def of(cls, offer: ProductOffer) -> Label:
        product, stock = offer.product, offer.stock
        rows = [
            "=" * WIDTH,
            product.name.upper().center(WIDTH),
            "=" * WIDTH,
            f"SKU        {product.sku}",
            f"Category   {product.category}",
            f"Weight     {product.weight_grams} g",
            f"Price      {offer.price_with_tax} EUR (tax included)",
            f"Stock      {stock.available} in {stock.warehouse}",
            "-" * WIDTH,
            ("IN STOCK" if offer.in_stock else "OUT OF STOCK").center(WIDTH),
            "=" * WIDTH,
        ]
        return cls("\n".join(rows) + "\n")
