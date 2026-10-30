import pytest

from shop.application.use_case.follow_product import FollowProduct
from shop.application.use_case.get_product import GetProduct
from shop.application.use_case.get_product_image import GetProductImage
from shop.application.use_case.place_order import PlaceOrder
from shop.application.use_case.render_label import RenderLabel
from shop.application.use_case.save_note import SaveNote
from shop.application.use_case.store_file import StoreFile
from shop.application.use_case.track_order import TrackOrder
from shop.domain.exception.product_not_found import ProductNotFound
from shop.domain.order.order_line import OrderLine
from shop.domain.order.order_request import OrderRequest
from shop.domain.order.tracking_event import TrackingStage
from tests.shop.fakes import (
    KETTLE,
    MUG,
    FixedInventory,
    FixedMarket,
    FixedPricing,
    InMemoryProducts,
    RecordingStore,
)

REQUEST = OrderRequest("acme", (OrderLine(KETTLE.sku, 1), OrderLine(MUG.sku, 2)))


def get_product() -> GetProduct:
    return GetProduct(InMemoryProducts(KETTLE, MUG), FixedInventory(), FixedPricing())


async def test_a_product_comes_with_its_stock_and_taxed_price() -> None:
    offer = await get_product().handle(KETTLE.sku)

    assert (offer.product, offer.stock.available) == (KETTLE, 7)


async def test_an_unknown_product_is_not_found() -> None:
    with pytest.raises(ProductNotFound):
        await get_product().handle("SKU-99999")


async def test_placing_an_order_prices_and_saves_it() -> None:
    orders = RecordingStore()

    order = await PlaceOrder(InMemoryProducts(KETTLE, MUG), FixedPricing(), orders).handle(REQUEST)

    assert orders.saved == [order]
    assert order.reference == REQUEST.reference


async def test_tracking_an_order_goes_through_every_stage_and_saves_it() -> None:
    orders = RecordingStore()
    track = TrackOrder(InMemoryProducts(KETTLE, MUG), FixedPricing(), FixedInventory(), orders)

    stages = [event.stage async for event in await track.handle(REQUEST)]

    assert stages == list(TrackingStage)
    assert len(orders.saved) == 1


async def test_tracking_an_order_with_an_unknown_product_fails_before_streaming() -> None:
    track = TrackOrder(InMemoryProducts(KETTLE), FixedPricing(), FixedInventory(), RecordingStore())

    with pytest.raises(ProductNotFound, match=MUG.sku):
        await track.handle(REQUEST)


async def test_following_a_product_streams_its_ticks() -> None:
    ticks = await FollowProduct(InMemoryProducts(KETTLE), FixedMarket()).handle(KETTLE.sku)

    assert [tick.sequence async for tick in ticks] == [1, 2]


async def test_the_image_label_file_and_note_use_cases() -> None:
    files, notes = RecordingStore(), RecordingStore()

    image = await GetProductImage(InMemoryProducts(KETTLE)).handle(KETTLE.sku)
    label = await RenderLabel(get_product()).handle(KETTLE.sku)
    stored = await StoreFile(files).handle(b"payload")
    note = await SaveNote(notes).handle("hello world")

    assert image == b"image of SKU-00001"
    assert "SMART KETTLE" in label.text
    assert (files.saved, notes.saved) == ([stored], [note])
