from collections.abc import Awaitable

import pytest

from shop_benchmark.application.benchmark import Benchmark
from shop_benchmark.application.benchmark_plan import BenchmarkPlan
from shop_benchmark.application.compare_frameworks import CompareFrameworks, NoRunsFound
from shop_benchmark.application.preflight import Preflight, PreflightFailed
from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.environment import Environment
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.server_usage import ServerUsage
from shop_benchmark.domain.service import Service
from shop_benchmark.workload.catalog import Workload
from tests.shop_benchmark.builders import FIXED_RATE, THROUGHPUT, measurement, report

ENDPOINTS = Workload("SKU-00042", 2, 64, 2).endpoints()[:2]
PLAN = BenchmarkPlan("http://127.0.0.1:8765", ENDPOINTS, (THROUGHPUT, FIXED_RATE), 1.0, 0.5)


class FakeTarget:
    def __init__(self, status: int = 200) -> None:
        self._status = status

    async def about(self) -> Service:
        return Service("web-framework", "1.0.0", "litestar", "2.25.0", "3.14.3", "granian")

    async def call(self, endpoint: Endpoint) -> Answer:
        return Answer(endpoint.name, self._status, endpoint.media_type, 12, "f")


class RecordingLoad:
    def __init__(self) -> None:
        self.runs: list[tuple[str, str, float]] = []

    async def run(self, endpoint: Endpoint, profile: LoadProfile, duration_seconds: float):
        self.runs.append((endpoint.name, profile.name, duration_seconds))
        return measurement(1000, 5.0)


class FixedProbe:
    async def during(self, work: Awaitable):
        return await work, ServerUsage(90.0, 100.0, 50.0, 55.0, 4)


class FixedEnvironment:
    def describe(self) -> Environment:
        return Environment("host", "cpu", 8, "system", "oha 1.16.0")


class MemoryStore:
    def __init__(self, runs=()) -> None:
        self.saved = []
        self._runs = list(runs)

    def save_run(self, report) -> list[str]:
        self.saved.append(report)
        return ["run.json"]

    def latest_runs(self):
        return self._runs

    def save_comparison(self, comparison) -> list[str]:
        self.saved.append(comparison)
        return ["final.json"]


class FakeClock:
    def __init__(self) -> None:
        self.slept: list[float] = []

    def now(self) -> str:
        return "2026-10-25T12:00:00+01:00"

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)


def benchmark(target, load, store, clock, logger) -> Benchmark:
    return Benchmark(target, load, FixedProbe(), FixedEnvironment(), store, clock, logger)


async def test_every_endpoint_runs_every_profile_after_a_warm_up(logger) -> None:
    load, store, clock = RecordingLoad(), MemoryStore(), FakeClock()

    run = await benchmark(FakeTarget(), load, store, clock, logger).run(PLAN)

    assert load.runs == [
        ("get_json", "throughput", 1.0),
        ("get_json", "throughput", 30),
        ("post_json", "throughput", 1.0),
        ("post_json", "throughput", 30),
        ("get_json", "fixed_rate", 1.0),
        ("get_json", "fixed_rate", 30),
        ("post_json", "fixed_rate", 1.0),
        ("post_json", "fixed_rate", 30),
    ]
    assert [(result.endpoint, result.profile) for result in run.results] == [
        ("get_json", "throughput"),
        ("post_json", "throughput"),
        ("get_json", "fixed_rate"),
        ("post_json", "fixed_rate"),
    ]
    assert run.service.framework == "litestar"
    assert all(result.usage is not None for result in run.results)
    assert store.saved == [run]
    assert clock.slept == [0.5] * 4


async def test_no_load_is_sent_when_an_endpoint_answers_wrongly(logger) -> None:
    load = RecordingLoad()

    with pytest.raises(PreflightFailed, match="status 500"):
        await benchmark(FakeTarget(status=500), load, MemoryStore(), FakeClock(), logger).run(PLAN)

    assert load.runs == []


async def test_preflight_returns_one_answer_per_endpoint() -> None:
    answers = await Preflight(FakeTarget()).check(ENDPOINTS)

    assert [answer.endpoint for answer in answers] == ["get_json", "post_json"]


def test_the_plan_tells_how_long_it_will_take() -> None:
    assert PLAN.runs == 4
    assert PLAN.duration_seconds == 30 * 4 + 4 * 1.5
    assert PLAN.describe()[-1] == "total       4 runs, about 2.1 min"


def test_comparing_needs_at_least_one_run(logger) -> None:
    with pytest.raises(NoRunsFound):
        CompareFrameworks(MemoryStore(), logger).run()


def test_comparing_saves_the_comparison_of_the_latest_runs(logger) -> None:
    store = MemoryStore(
        [report("fastapi", {"get_json": (1, 1)}), report("litestar", {"get_json": (2, 1)})]
    )

    comparison = CompareFrameworks(store, logger).run()

    assert comparison.frameworks == ["fastapi", "litestar"]
    assert store.saved == [comparison]
