from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoadProfile:
    name: str
    connections: int
    duration_seconds: float
    rate_per_second: int | None = None

    @property
    def is_fixed_rate(self) -> bool:
        return self.rate_per_second is not None

    @property
    def description(self) -> str:
        rate = f"{self.rate_per_second} req/s over " if self.is_fixed_rate else ""
        return f"{rate}{self.connections} connections for {self.duration_seconds:g} s"
