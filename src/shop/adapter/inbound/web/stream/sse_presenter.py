import json
from collections.abc import AsyncIterator, Mapping

from shop.domain.market.tick import Tick
from shop.domain.order.tracking_event import TrackingEvent


class SsePresenter:
    @staticmethod
    async def ticks(ticks: AsyncIterator[Tick]) -> AsyncIterator[bytes]:
        count = 0
        async for tick in ticks:
            count += 1
            yield _frame(
                "tick",
                {
                    "sku": tick.sku,
                    "sequence": tick.sequence,
                    "price": str(tick.price),
                    "available": tick.available,
                },
            )
        yield _frame("end", {"events": count})

    @staticmethod
    async def tracking(events: AsyncIterator[TrackingEvent]) -> AsyncIterator[bytes]:
        count = 0
        async for event in events:
            count += 1
            yield _frame(
                "tracking",
                {"stage": event.stage.value, "reference": event.reference, "detail": event.detail},
            )
        yield _frame("end", {"events": count})


def _frame(event: str, data: Mapping[str, object]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n".encode()
