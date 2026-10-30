from dataclasses import dataclass

from shop_benchmark.domain.endpoint import Endpoint


@dataclass(frozen=True, slots=True)
class Answer:
    endpoint: str
    status: int
    media_type: str
    size: int
    fingerprint: str

    def problems(self, endpoint: Endpoint) -> list[str]:
        problems = []
        if self.status != 200:
            problems.append(f"{endpoint.name}: status {self.status}, expected 200")
        if not self.media_type.startswith(endpoint.media_type):
            problems.append(
                f"{endpoint.name}: media type {self.media_type!r}, expected {endpoint.media_type!r}"
            )
        if self.size == 0:
            problems.append(f"{endpoint.name}: empty body")
        return problems
