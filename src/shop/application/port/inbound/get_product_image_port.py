from typing import Protocol


class GetProductImagePort(Protocol):
    async def handle(self, sku: str) -> bytes: ...
