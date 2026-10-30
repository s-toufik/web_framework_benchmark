from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from pycraftcore.repository.port import AsyncRepository

from shop.domain.product.product import Product

COLUMNS: str = "sku, name, category, price_cents, weight_grams"


class SqliteProductRepository:
    def __init__(self, repository: AsyncRepository) -> None:
        self._repository = repository

    async def product(self, sku: str) -> Product | None:
        rows = await self._repository.execute(
            f"SELECT {COLUMNS} FROM products WHERE sku = ?", (sku,)
        )
        return _product(rows[0]) if rows else None

    async def products(self, skus: Sequence[str]) -> list[Product]:
        if not skus:
            return []
        placeholders = ", ".join("?" for _ in skus)
        rows = await self._repository.execute(
            f"SELECT {COLUMNS} FROM products WHERE sku IN ({placeholders}) ORDER BY sku",
            tuple(skus),
        )
        return [_product(row) for row in rows]

    async def image(self, sku: str) -> bytes | None:
        rows = await self._repository.execute("SELECT image FROM products WHERE sku = ?", (sku,))
        return bytes(rows[0]["image"]) if rows else None


def _product(row: dict[str, Any]) -> Product:
    return Product(
        sku=row["sku"],
        name=row["name"],
        category=row["category"],
        price=Decimal(row["price_cents"]) / 100,
        weight_grams=row["weight_grams"],
    )
