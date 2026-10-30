from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse

from pycraftcore.logger import configure_logging
from pycraftcore.logger.adapter import StandardLogger
from pycraftcore.logger.port import Logger

from shop_benchmark.adapter.clock.system_clock import SystemClock
from shop_benchmark.adapter.environment.machine_environment import MachineEnvironment
from shop_benchmark.adapter.http.http_target import HttpTarget
from shop_benchmark.adapter.oha.oha_load_generator import OhaLoadGenerator
from shop_benchmark.adapter.probe.process_probe import NoProbe, ProcessProbe
from shop_benchmark.adapter.report.file_report_store import FileReportStore
from shop_benchmark.application.benchmark import Benchmark
from shop_benchmark.application.benchmark_plan import BenchmarkPlan
from shop_benchmark.application.compare_frameworks import CompareFrameworks
from shop_benchmark.application.port.server_probe import ServerProbe
from shop_benchmark.configuration.control_panel import ControlPanel

LOCAL_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1", "0.0.0.0"})


class UnknownEndpoints(Exception):
    def __init__(self, unknown: list[str], known: list[str]) -> None:
        super().__init__(f"Unknown endpoints {unknown}; choose among {known}")


class BenchmarkContainer:
    def __init__(self, panel: ControlPanel) -> None:
        self._panel = panel

    @cached_property
    def logger(self) -> Logger:
        configure_logging("INFO")
        return StandardLogger()

    @cached_property
    def plan(self) -> BenchmarkPlan:
        endpoints = self._panel.workload.to_domain().endpoints()
        known = [endpoint.name for endpoint in endpoints]
        unknown = [name for name in self._panel.endpoints if name not in known]
        if unknown:
            raise UnknownEndpoints(unknown, known)
        chosen = self._panel.endpoints or known
        return BenchmarkPlan(
            base_url=self._panel.target.base_url,
            endpoints=tuple(endpoint for endpoint in endpoints if endpoint.name in chosen),
            profiles=tuple(profile.to_domain() for profile in self._panel.load.profiles),
            warmup_seconds=self._panel.load.warmup_seconds,
            pause_seconds=self._panel.load.pause_seconds,
        )

    def benchmark(self) -> Benchmark:
        return Benchmark(
            target=HttpTarget(self._panel.target.base_url, self._panel.target.timeout_seconds),
            load=OhaLoadGenerator(self._panel.target.base_url, self._panel.load.oha),
            probe=self._probe(),
            environment=MachineEnvironment(self._panel.load.oha),
            store=self._store,
            clock=SystemClock(),
            logger=self.logger,
        )

    def compare(self) -> CompareFrameworks:
        return CompareFrameworks(self._store, self.logger)

    @cached_property
    def _store(self) -> FileReportStore:
        return FileReportStore(Path(self._panel.output_dir), SystemClock())

    def _probe(self) -> ServerProbe:
        url = urlparse(self._panel.target.base_url)
        if not self._panel.probe.enabled or url.hostname not in LOCAL_HOSTS or url.port is None:
            return NoProbe()
        return ProcessProbe(url.port, self._panel.probe.interval_seconds)
