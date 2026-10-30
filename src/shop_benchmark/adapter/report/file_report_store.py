import json
from pathlib import Path

from shop_benchmark.adapter.report.comparison_markdown import render_comparison
from shop_benchmark.adapter.report.report_codec import decode_run, encode_comparison, encode_run
from shop_benchmark.adapter.report.run_markdown import render_run
from shop_benchmark.application.port.clock import Clock
from shop_benchmark.domain.comparison import Comparison
from shop_benchmark.domain.run_report import RunReport

FINAL_PREFIX: str = "final_"


class FileReportStore:
    def __init__(self, output_dir: Path, clock: Clock) -> None:
        self._output_dir = output_dir
        self._clock = clock

    def save_run(self, report: RunReport) -> list[str]:
        folder = self._output_dir / report.framework
        stem = folder / _stamp(report.started_at)
        return self._write(stem, json.dumps(encode_run(report), indent=2), render_run(report))

    def latest_runs(self) -> list[RunReport]:
        if not self._output_dir.is_dir():
            return []
        reports = []
        for folder in sorted(path for path in self._output_dir.iterdir() if path.is_dir()):
            runs = sorted(folder.glob("*.json"))
            if runs:
                reports.append(decode_run(json.loads(runs[-1].read_text())))
        return reports

    def save_comparison(self, comparison: Comparison) -> list[str]:
        generated_at = self._clock.now()
        stem = self._output_dir / f"{FINAL_PREFIX}{_stamp(generated_at)}"
        return self._write(
            stem,
            json.dumps(encode_comparison(comparison, generated_at), indent=2),
            render_comparison(comparison, generated_at),
        )

    @staticmethod
    def _write(stem: Path, json_text: str, markdown: str) -> list[str]:
        stem.parent.mkdir(parents=True, exist_ok=True)
        json_path, markdown_path = stem.with_suffix(".json"), stem.with_suffix(".md")
        json_path.write_text(json_text + "\n")
        markdown_path.write_text(markdown)
        return [str(json_path), str(markdown_path)]


def _stamp(moment: str) -> str:
    return moment[:19].replace(":", "-")
