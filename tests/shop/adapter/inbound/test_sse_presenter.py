from collections.abc import AsyncIterator
from decimal import Decimal

from shop.adapter.inbound.web.stream.sse_presenter import SsePresenter
from shop.domain.market.tick import Tick
from shop.domain.order.tracking_event import TrackingEvent, TrackingStage


async def _from(*items):
    for item in items:
        yield item


async def _collect(frames: AsyncIterator[bytes]) -> list[bytes]:
    return [frame async for frame in frames]


async def test_ticks_become_tick_frames_and_an_end_frame() -> None:
    frames = await _collect(SsePresenter.ticks(_from(Tick("SKU-00001", 1, Decimal("9.50"), 3))))

    assert frames == [
        b'event: tick\ndata: {"sku":"SKU-00001","sequence":1,"price":"9.50","available":3}\n\n',
        b'event: end\ndata: {"events":1}\n\n',
    ]


async def test_tracking_events_become_tracking_frames() -> None:
    event = TrackingEvent(TrackingStage.PRICED, "ORD-1", "total 9.50 EUR")

    frames = await _collect(SsePresenter.tracking(_from(event)))

    assert frames[0] == (
        b'event: tracking\ndata: {"stage":"priced","reference":"ORD-1","detail":"total 9.50 EUR"}\n\n'
    )
