from typing import Protocol

from shop_benchmark.domain.environment import Environment


class EnvironmentProbe(Protocol):
    def describe(self) -> Environment: ...
