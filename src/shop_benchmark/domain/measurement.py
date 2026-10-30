from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Latency:
    mean_ms: float
    p50_ms: float
    p90_ms: float
    p99_ms: float
    p999_ms: float
    max_ms: float


@dataclass(frozen=True, slots=True)
class Measurement:
    requests: int
    requests_per_second: float
    bytes_per_second: float
    latency: Latency
    first_byte: Latency
    status_codes: Mapping[str, int]
    errors: Mapping[str, int]

    @property
    def successes(self) -> int:
        return sum(count for status, count in self.status_codes.items() if status.startswith("2"))

    @property
    def failures(self) -> int:
        return self.requests - self.successes + sum(self.errors.values())

    @property
    def error_rate(self) -> float:
        attempts = self.requests + sum(self.errors.values())
        return self.failures / attempts if attempts else 0.0
