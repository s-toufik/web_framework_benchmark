from collections.abc import Awaitable
from typing import Protocol

from shop_benchmark.domain.server_usage import ServerUsage


class ServerProbe(Protocol):
    async def during[T](self, work: Awaitable[T]) -> tuple[T, ServerUsage | None]: ...
