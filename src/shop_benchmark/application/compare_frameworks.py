from pycraftcore.logger.port import Logger

from shop_benchmark.application.port.report_store import ReportStore
from shop_benchmark.domain.comparison import Comparison


class NoRunsFound(Exception):
    def __init__(self) -> None:
        super().__init__(
            "No benchmark run found: run the benchmark against at least one framework first"
        )


class CompareFrameworks:
    def __init__(self, store: ReportStore, logger: Logger) -> None:
        self._store = store
        self._logger = logger

    def run(self) -> Comparison:
        reports = self._store.latest_runs()
        if not reports:
            raise NoRunsFound()
        comparison = Comparison.of(reports)
        self._logger.info(f"Comparing {', '.join(report.service.title for report in reports)}")
        for path in self._store.save_comparison(comparison):
            self._logger.info(f"Report written: {path}")
        return comparison
