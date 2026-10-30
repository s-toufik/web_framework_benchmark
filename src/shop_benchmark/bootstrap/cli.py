import argparse
import asyncio
import shutil
import sys
from pathlib import Path

import httpx

from shop_benchmark.adapter.oha.oha_load_generator import LoadGeneratorFailed
from shop_benchmark.application.compare_frameworks import NoRunsFound
from shop_benchmark.application.preflight import PreflightFailed
from shop_benchmark.bootstrap.container import BenchmarkContainer, UnknownEndpoints
from shop_benchmark.configuration.control_panel import ControlPanel, Overrides

DEFAULT_PANEL: Path = Path(__file__).resolve().parents[1] / "control_panel.json"


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    panel = _overrides(arguments).apply(ControlPanel.load_file(Path(arguments.panel)))
    container = BenchmarkContainer(panel)
    try:
        if arguments.command == "report":
            container.compare().run()
            return 0
        print("\n".join(container.plan.describe()))
        if arguments.dry_run:
            return 0
        if shutil.which(panel.load.oha) is None:
            print(f"{panel.load.oha} is not installed: brew install oha", file=sys.stderr)
            return 1
        asyncio.run(container.benchmark().run(container.plan))
        return 0
    except httpx.ConnectError:
        print(
            f"Nothing answers at {panel.target.base_url}: start a framework first (make run_litestar)",
            file=sys.stderr,
        )
    except (PreflightFailed, LoadGeneratorFailed, NoRunsFound, UnknownEndpoints) as error:
        print(str(error), file=sys.stderr)
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shop_benchmark",
        description="Benchmark the shop served by one web framework, then compare the frameworks.",
    )
    parser.add_argument(
        "command",
        choices=["run", "report"],
        help="run: benchmark the framework now serving; report: compare the latest run of each framework",
    )
    parser.add_argument("--panel", default=str(DEFAULT_PANEL), help="control panel JSON")
    parser.add_argument("--base-url", help="where the shop answers")
    parser.add_argument("--duration", type=float, help="seconds measured per endpoint and profile")
    parser.add_argument("--warmup", type=float, help="seconds of warm-up before each measured run")
    parser.add_argument("--connections", type=int, help="concurrent connections for every profile")
    parser.add_argument(
        "--endpoints", help="comma-separated endpoint names, e.g. get_json,post_stream"
    )
    parser.add_argument("--profiles", help="comma-separated profile names, e.g. throughput")
    parser.add_argument("--output-dir", help="where reports are written")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and stop")
    return parser


def _overrides(arguments: argparse.Namespace) -> Overrides:
    return Overrides(
        base_url=arguments.base_url,
        duration_seconds=arguments.duration,
        warmup_seconds=arguments.warmup,
        connections=arguments.connections,
        endpoints=arguments.endpoints.split(",") if arguments.endpoints else None,
        profiles=arguments.profiles.split(",") if arguments.profiles else None,
        output_dir=arguments.output_dir,
    )
