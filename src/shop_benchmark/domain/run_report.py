from dataclasses import dataclass

from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.environment import Environment
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.service import Service


@dataclass(frozen=True, slots=True)
class RunReport:
    service: Service
    environment: Environment
    base_url: str
    started_at: str
    finished_at: str
    warmup_seconds: float
    profiles: tuple[LoadProfile, ...]
    answers: tuple[Answer, ...]
    results: tuple[EndpointResult, ...]

    @property
    def framework(self) -> str:
        return self.service.framework

    def results_for(self, profile: str) -> list[EndpointResult]:
        return [result for result in self.results if result.profile == profile]

    def result(self, endpoint: str, profile: str) -> EndpointResult | None:
        return next(
            (
                result
                for result in self.results
                if result.endpoint == endpoint and result.profile == profile
            ),
            None,
        )
