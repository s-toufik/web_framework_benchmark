from typing import Final

from pycraftcore.repository.port import AsyncRepository

TABLES: Final[dict[str, str]] = {
    "products": (
        "CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,"
        " price_cents INTEGER NOT NULL, weight_grams INTEGER NOT NULL, image BLOB NOT NULL)"
    ),
    "orders": (
        "CREATE TABLE orders (reference TEXT PRIMARY KEY, customer TEXT NOT NULL,"
        " items INTEGER NOT NULL, total_cents INTEGER NOT NULL, lines TEXT NOT NULL)"
    ),
    "files": "CREATE TABLE files (name TEXT PRIMARY KEY, size INTEGER NOT NULL, content BLOB NOT NULL)",
    "notes": (
        "CREATE TABLE notes (digest TEXT PRIMARY KEY, words INTEGER NOT NULL, text TEXT NOT NULL)"
    ),
}


async def reset_schema(repository: AsyncRepository) -> None:
    for table, ddl in TABLES.items():
        await repository.execute(f"DROP TABLE IF EXISTS {table}")
        await repository.execute(ddl)
