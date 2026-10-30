from collections.abc import Sequence

from shop_benchmark.application.port.target import Target
from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint import Endpoint


class PreflightFailed(Exception):
    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__("Preflight failed:\n" + "\n".join(f"- {problem}" for problem in problems))
        self.problems = list(problems)


class Preflight:
    def __init__(self, target: Target) -> None:
        self._target = target

    async def check(self, endpoints: Sequence[Endpoint]) -> tuple[Answer, ...]:
        answers = tuple([await self._target.call(endpoint) for endpoint in endpoints])
        problems = [
            problem
            for endpoint, answer in zip(endpoints, answers, strict=True)
            for problem in answer.problems(endpoint)
        ]
        if problems:
            raise PreflightFailed(problems)
        return answers
