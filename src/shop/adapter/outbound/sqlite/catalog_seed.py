import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched
from typing import Final

from pycraftcore.repository.port import AsyncRepository

from shop.adapter.outbound.deterministic import number

ADJECTIVES: Final[tuple[str, ...]] = (
    "Classic",
    "Compact",
    "Deluxe",
    "Eco",
    "Essential",
    "Heavy",
    "Light",
    "Modern",
    "Nordic",
    "Premium",
    "Rugged",
    "Smart",
    "Solid",
    "Urban",
    "Vintage",
    "Wireless",
)
NOUNS: Final[tuple[str, ...]] = (
    "Backpack",
    "Blender",
    "Chair",
    "Desk Lamp",
    "Headphones",
    "Jacket",
    "Kettle",
    "Keyboard",
    "Mug",
    "Notebook",
    "Speaker",
    "Sneakers",
    "Tent",
    "Thermos",
    "Watch",
    "Water Bottle",
)
CATEGORIES: Final[tuple[str, ...]] = ("home", "kitchen", "office", "outdoor", "audio", "apparel")
ROWS_PER_INSERT: Final[int] = 100


def sku_of(index: int) -> str:
    return f"SKU-{index:05d}"


@dataclass(frozen=True, slots=True)
class CatalogSeed:
    seed: int
    products: int
    image_bytes: int

    async def plant(self, repository: AsyncRepository) -> None:
        for rows in batched(self.rows(), ROWS_PER_INSERT):
            placeholders = ", ".join("(?, ?, ?, ?, ?, ?)" for _ in rows)
            values = tuple(value for row in rows for value in row)
            await repository.execute(f"INSERT INTO products VALUES {placeholders}", values)

    def rows(self) -> Iterator[tuple[str, str, str, int, int, bytes]]:
        for index in range(1, self.products + 1):
            sku = sku_of(index)
            yield (
                sku,
                f"{ADJECTIVES[self._pick(sku, 'adjective')]} {NOUNS[self._pick(sku, 'noun')]}",
                CATEGORIES[number(self.seed, sku, "category") % len(CATEGORIES)],
                199 + number(self.seed, sku, "price") % 49_800,
                50 + number(self.seed, sku, "weight") % 5_000,
                hashlib.shake_256(f"{self.seed}:{sku}:image".encode()).digest(self.image_bytes),
            )

    def _pick(self, sku: str, field: str) -> int:
        return number(self.seed, sku, field) % 16
