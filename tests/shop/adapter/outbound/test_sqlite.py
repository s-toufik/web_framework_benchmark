from decimal import Decimal

import pytest
from pycraftcore.repository.adapter import SqliteRepositoryFactory
from pycraftcore.repository.adapter.sql.sqlite import SqliteConnector

from shop.adapter.outbound.sqlite.catalog_seed import CatalogSeed, sku_of
from shop.adapter.outbound.sqlite.shop_schema import reset_schema
from shop.adapter.outbound.sqlite.sqlite_file_repository import SqliteFileRepository
from shop.adapter.outbound.sqlite.sqlite_note_repository import SqliteNoteRepository
from shop.adapter.outbound.sqlite.sqlite_order_repository import SqliteOrderRepository
from shop.adapter.outbound.sqlite.sqlite_product_repository import SqliteProductRepository
from shop.domain.file.stored_file import StoredFile
from shop.domain.note.note import Note
from shop.domain.order.order import Order
from shop.domain.order.order_line import OrderLine
from shop.domain.order.order_request import OrderRequest
from tests.shop.fakes import QUOTE

SEED = CatalogSeed(seed=7, products=120, image_bytes=1024)


@pytest.fixture
async def repository(tmp_path):
    factory = SqliteRepositoryFactory(
        SqliteConnector(path=str(tmp_path), default_name="shop", max_pool_size=2)
    )
    repository = await factory.connect()
    await reset_schema(repository)
    await SEED.plant(repository)
    yield repository
    await factory.disconnect()


def test_the_seed_is_the_same_for_the_same_settings() -> None:
    assert list(SEED.rows()) == list(CatalogSeed(7, 120, 1024).rows())
    assert list(SEED.rows()) != list(CatalogSeed(8, 120, 1024).rows())


async def test_every_seeded_product_can_be_read_with_its_image(repository) -> None:
    products = SqliteProductRepository(repository)

    first = await products.product(sku_of(1))
    image = await products.image(sku_of(120))
    found = await products.products([sku_of(3), sku_of(2), "SKU-99999"])

    assert first is not None and first.price > Decimal("1.98")
    assert image is not None and len(image) == 1024
    assert [product.sku for product in found] == [sku_of(2), sku_of(3)]
    assert await products.product("SKU-99999") is None


async def test_orders_files_and_notes_are_stored_once_per_content(repository) -> None:
    products = SqliteProductRepository(repository)
    request = OrderRequest("acme", (OrderLine(sku_of(1), 2),))
    order = Order.price(request, {sku_of(1): await products.product(sku_of(1))}, QUOTE)

    for _ in range(2):
        await SqliteOrderRepository(repository).save(order)
        await SqliteFileRepository(repository).save(StoredFile.of(b"data"), b"data")
        await SqliteNoteRepository(repository).save(Note.of("hello"))

    counts = [
        (await repository.execute(f"SELECT COUNT(*) AS n FROM {table}"))[0]["n"]
        for table in ("orders", "files", "notes")
    ]
    assert counts == [1, 1, 1]
