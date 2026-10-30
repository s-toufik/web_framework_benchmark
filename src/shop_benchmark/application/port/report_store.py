from typing import Protocol

from shop_benchmark.domain.comparison import Comparison
from shop_benchmark.domain.run_report import RunReport


class ReportStore(Protocol):
    def save_run(self, report: RunReport) -> list[str]: ...

    def latest_runs(self) -> list[RunReport]: ...

    def save_comparison(self, comparison: Comparison) -> list[str]: ...
