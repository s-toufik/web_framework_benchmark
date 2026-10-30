from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True, slots=True)
class ServerUsage:
    cpu_percent_mean: float
    cpu_percent_max: float
    memory_mb_mean: float
    memory_mb_max: float
    samples: int

    @classmethod
    def of(cls, samples: Sequence[tuple[float, float]]) -> ServerUsage | None:
        if not samples:
            return None
        cpu = [sample[0] for sample in samples]
        memory = [sample[1] for sample in samples]
        return cls(fmean(cpu), max(cpu), fmean(memory), max(memory), len(samples))
