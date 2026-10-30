from typing import Protocol

from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.measurement import Measurement


class LoadGenerator(Protocol):
    async def run(
        self, endpoint: Endpoint, profile: LoadProfile, duration_seconds: float
    ) -> Measurement: ...
