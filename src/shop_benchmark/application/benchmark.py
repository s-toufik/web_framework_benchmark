from pycraftcore.logger.port import Logger

from shop_benchmark.application.benchmark_plan import BenchmarkPlan
from shop_benchmark.application.port.clock import Clock
from shop_benchmark.application.port.environment_probe import EnvironmentProbe
from shop_benchmark.application.port.load_generator import LoadGenerator
from shop_benchmark.application.port.report_store import ReportStore
from shop_benchmark.application.port.server_probe import ServerProbe
from shop_benchmark.application.port.target import Target
from shop_benchmark.application.preflight import Preflight
from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.run_report import RunReport


class Benchmark:
    def __init__(
        self,
        target: Target,
        load: LoadGenerator,
        probe: ServerProbe,
        environment: EnvironmentProbe,
        store: ReportStore,
        clock: Clock,
        logger: Logger,
    ) -> None:
        self._target = target
        self._load = load
        self._probe = probe
        self._environment = environment
        self._store = store
        self._clock = clock
        self._logger = logger

    async def run(self, plan: BenchmarkPlan) -> RunReport:
        started_at = self._clock.now()
        service = await self._target.about()
        self._logger.info(
            f"Benchmarking {service.title} served by {service.server} at {plan.base_url}"
        )
        answers = await Preflight(self._target).check(plan.endpoints)
        self._logger.info(f"Preflight passed for {len(answers)} endpoints")

        results = []
        for profile in plan.profiles:
            for endpoint in plan.endpoints:
                results.append(await self._measure(endpoint, profile, plan))

        report = RunReport(
            service=service,
            environment=self._environment.describe(),
            base_url=plan.base_url,
            started_at=started_at,
            finished_at=self._clock.now(),
            warmup_seconds=plan.warmup_seconds,
            profiles=plan.profiles,
            answers=answers,
            results=tuple(results),
        )
        for path in self._store.save_run(report):
            self._logger.info(f"Report written: {path}")
        return report

    async def _measure(
        self, endpoint: Endpoint, profile: LoadProfile, plan: BenchmarkPlan
    ) -> EndpointResult:
        if plan.warmup_seconds > 0:
            await self._load.run(endpoint, profile, plan.warmup_seconds)
        measurement, usage = await self._probe.during(
            self._load.run(endpoint, profile, profile.duration_seconds)
        )
        self._logger.info(
            f"{profile.name:<12} {endpoint.label:<12} {measurement.requests_per_second:>9.0f} req/s"
            f"  p50 {measurement.latency.p50_ms:7.2f} ms  p99 {measurement.latency.p99_ms:7.2f} ms"
            f"  failures {measurement.failures}"
        )
        await self._clock.sleep(plan.pause_seconds)
        return EndpointResult(
            endpoint=endpoint.name,
            kind=endpoint.kind,
            method=endpoint.method,
            path=endpoint.path,
            profile=profile.name,
            measurement=measurement,
            usage=usage,
        )
