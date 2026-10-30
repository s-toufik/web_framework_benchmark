from collections.abc import AsyncIterator
from typing import Protocol

from shop.domain.market.tick import Tick


class FollowProductPort(Protocol):
    async def handle(self, sku: str) -> AsyncIterator[Tick]: ...
