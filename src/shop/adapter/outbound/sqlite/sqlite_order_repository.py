import json

from pycraftcore.repository.port import AsyncRepository

from shop.domain.order.order import Order


class SqliteOrderRepository:
    def __init__(self, repository: AsyncRepository) -> None:
        self._repository = repository

    async def save(self, order: Order) -> None:
        lines = json.dumps(
            [[line.sku, line.quantity, str(line.line_total)] for line in order.lines],
            separators=(",", ":"),
        )
        await self._repository.execute(
            "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?)",
            (order.reference, order.customer, order.items, int(order.total * 100), lines),
        )
