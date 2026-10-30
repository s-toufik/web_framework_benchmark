import json
from dataclasses import replace
from pathlib import Path

from shop_benchmark.adapter.report.comparison_markdown import render_comparison
from shop_benchmark.adapter.report.file_report_store import FileReportStore
from shop_benchmark.adapter.report.report_codec import decode_run, encode_comparison, encode_run
from shop_benchmark.adapter.report.run_markdown import render_run
from shop_benchmark.domain.comparison import Comparison
from tests.shop_benchmark.builders import report

FASTAPI = report("fastapi", {"get_json": (1000, 9.0), "get_text": (3000, 2.0)})
LITESTAR = report("litestar", {"get_json": (2000, 6.0), "get_text": (1500, 4.0)})


class FixedClock:
    def now(self) -> str:
        return "2026-10-25T12:00:00+01:00"

    async def sleep(self, seconds: float) -> None:
        return None


def test_a_run_report_survives_its_json_round_trip() -> None:
    assert decode_run(json.loads(json.dumps(encode_run(FASTAPI)))) == FASTAPI


def test_a_run_report_shows_every_profile_and_the_preflight() -> None:
    markdown = render_run(FASTAPI)

    assert markdown.startswith("# Benchmark: fastapi 1.0")
    assert "## throughput: 64 connections for 30 s" in markdown
    assert "## fixed_rate: 500 req/s over 64 connections for 30 s" in markdown
    assert "| GET json | `GET /v1/get_json` | 1 000 |" in markdown
    assert "## Preflight answers" in markdown


def test_the_comparison_marks_the_best_and_how_far_behind_the_others_are() -> None:
    markdown = render_comparison(Comparison.of([FASTAPI, LITESTAR]), "2026-10-25T12:00:00+01:00")

    assert "# Framework comparison: fastapi, litestar" in markdown
    assert "| GET json | 1 000 (-50 %) | **2 000** | litestar |" in markdown
    assert "Every endpoint returned the same bytes on every framework" in markdown
    assert "## Server resources" in markdown


def test_the_final_json_holds_every_run_and_the_comparison() -> None:
    final = encode_comparison(Comparison.of([FASTAPI, LITESTAR]), "now")

    assert [run["service"]["framework"] for run in final["frameworks"]] == ["fastapi", "litestar"]
    assert {matchup["winner"] for matchup in final["matchups"]} == {"fastapi", "litestar"}
    assert set(final["scores"]) == {"throughput", "fixed_rate"}


def test_the_store_keeps_each_run_and_compares_the_latest_of_each_framework(tmp_path) -> None:
    store = FileReportStore(tmp_path, FixedClock())
    older = replace(
        report("fastapi", {"get_json": (10, 9.0)}), started_at="2026-10-25T09:00:00+01:00"
    )
    for run in (older, FASTAPI, LITESTAR):
        store.save_run(run)

    latest = store.latest_runs()
    written = store.save_comparison(Comparison.of(latest))

    assert latest == [FASTAPI, LITESTAR]
    assert len(list((tmp_path / "fastapi").glob("*.json"))) == 2
    assert sorted(Path(path).name for path in written) == [
        "final_2026-10-25T12-00-00.json",
        "final_2026-10-25T12-00-00.md",
    ]


def test_a_slower_framework_shows_how_much_slower_it_is_at_a_fixed_rate() -> None:
    markdown = render_comparison(Comparison.of([FASTAPI, LITESTAR]), "now")

    assert "| GET json | 9.00 (+50 %) | **6.00** | litestar |" in markdown
