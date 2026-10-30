from typing import Protocol

from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.service import Service


class Target(Protocol):
    async def about(self) -> Service: ...

    async def call(self, endpoint: Endpoint) -> Answer: ...
