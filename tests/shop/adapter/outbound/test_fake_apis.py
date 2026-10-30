from decimal import Decimal

from shop.adapter.outbound.api.fake_inventory_api import FakeInventoryApi
from shop.adapter.outbound.api.fake_market_feed import FakeMarketFeed
from shop.adapter.outbound.api.fake_pricing_api import FakePricingApi
from shop.domain.order.order_line import OrderLine
from tests.shop.fakes import KETTLE


async def test_the_inventory_answers_the_same_stock_and_reservation_every_time() -> None:
    inventory = FakeInventoryApi(latency_seconds=0)
    lines = (OrderLine(KETTLE.sku, 2),)

    assert await inventory.stock(KETTLE.sku) == await inventory.stock(KETTLE.sku)
    assert await inventory.reserve("ORD-1", lines) == await inventory.reserve("ORD-1", lines)
    assert (await inventory.reserve("ORD-1", lines)).startswith("RSV-")


async def test_pricing_gives_volume_discounts() -> None:
    pricing = FakePricingApi(latency_seconds=0)

    small = await pricing.quote("someone", (OrderLine(KETTLE.sku, 1),))
    large = await pricing.quote("someone", (OrderLine(KETTLE.sku, 30),))

    assert small.tax_rate == Decimal("0.20")
    assert large.discount_rate - small.discount_rate == Decimal("0.10")


async def test_the_market_feed_streams_the_same_ticks_every_time() -> None:
    feed = FakeMarketFeed(interval_seconds=0, ticks=5)

    first = [tick async for tick in feed.ticks(KETTLE)]
    second = [tick async for tick in feed.ticks(KETTLE)]

    assert first == second
    assert [tick.sequence for tick in first] == [1, 2, 3, 4, 5]
