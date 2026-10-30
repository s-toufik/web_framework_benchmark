from dataclasses import dataclass

from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.load_profile import LoadProfile


@dataclass(frozen=True, slots=True)
class BenchmarkPlan:
    base_url: str
    endpoints: tuple[Endpoint, ...]
    profiles: tuple[LoadProfile, ...]
    warmup_seconds: float
    pause_seconds: float

    @property
    def runs(self) -> int:
        return len(self.endpoints) * len(self.profiles)

    @property
    def duration_seconds(self) -> float:
        measured = sum(profile.duration_seconds for profile in self.profiles) * len(self.endpoints)
        return measured + self.runs * (self.warmup_seconds + self.pause_seconds)

    def describe(self) -> list[str]:
        lines = [f"target      {self.base_url}"]
        lines += [
            f"endpoint    {endpoint.label:<12} {endpoint.method} {endpoint.path}"
            for endpoint in self.endpoints
        ]
        lines += [
            f"profile     {profile.name:<12} {profile.description}" for profile in self.profiles
        ]
        lines.append(
            f"warm-up     {self.warmup_seconds:g} s before each run, {self.pause_seconds:g} s pause after"
        )
        lines.append(f"total       {self.runs} runs, about {self.duration_seconds / 60:.1f} min")
        return lines
