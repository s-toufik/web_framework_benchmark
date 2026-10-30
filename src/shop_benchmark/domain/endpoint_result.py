from dataclasses import dataclass

from shop_benchmark.domain.endpoint import EndpointKind
from shop_benchmark.domain.measurement import Measurement
from shop_benchmark.domain.server_usage import ServerUsage


@dataclass(frozen=True, slots=True)
class EndpointResult:
    endpoint: str
    kind: EndpointKind
    method: str
    path: str
    profile: str
    measurement: Measurement
    usage: ServerUsage | None

    @property
    def label(self) -> str:
        return f"{self.method} {self.kind.value}"
