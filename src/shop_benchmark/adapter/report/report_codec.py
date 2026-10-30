from dataclasses import asdict
from typing import Any

from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.comparison import Comparison
from shop_benchmark.domain.endpoint import EndpointKind
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.environment import Environment
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.measurement import Latency, Measurement
from shop_benchmark.domain.run_report import RunReport
from shop_benchmark.domain.server_usage import ServerUsage
from shop_benchmark.domain.service import Service


def encode_run(report: RunReport) -> dict[str, Any]:
    return asdict(report)


def decode_run(data: dict[str, Any]) -> RunReport:
    return RunReport(
        service=Service(**data["service"]),
        environment=Environment(**data["environment"]),
        base_url=data["base_url"],
        started_at=data["started_at"],
        finished_at=data["finished_at"],
        warmup_seconds=data["warmup_seconds"],
        profiles=tuple(LoadProfile(**profile) for profile in data["profiles"]),
        answers=tuple(Answer(**answer) for answer in data["answers"]),
        results=tuple(_result(result) for result in data["results"]),
    )


def encode_comparison(comparison: Comparison, generated_at: str) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "frameworks": [encode_run(report) for report in comparison.reports],
        "scores": {
            profile.name: [asdict(score) for score in comparison.scores(profile.name)]
            for profile in comparison.profiles
        },
        "matchups": [
            {
                "endpoint": matchup.endpoint,
                "label": matchup.label,
                "profile": matchup.profile.name,
                "ranked_by": "p99_ms" if matchup.profile.is_fixed_rate else "requests_per_second",
                "winner": matchup.winner,
                "standings": [
                    {
                        "framework": standing.framework,
                        "ratio": round(standing.ratio, 4),
                        "requests_per_second": standing.result.measurement.requests_per_second,
                        "p50_ms": standing.result.measurement.latency.p50_ms,
                        "p99_ms": standing.result.measurement.latency.p99_ms,
                        "failures": standing.result.measurement.failures,
                    }
                    for standing in matchup.standings
                ],
            }
            for matchup in comparison.matchups
        ],
        "mismatched_answers": comparison.mismatched_answers(),
    }


def _result(data: dict[str, Any]) -> EndpointResult:
    measurement = data["measurement"]
    return EndpointResult(
        endpoint=data["endpoint"],
        kind=EndpointKind(data["kind"]),
        method=data["method"],
        path=data["path"],
        profile=data["profile"],
        measurement=Measurement(
            requests=measurement["requests"],
            requests_per_second=measurement["requests_per_second"],
            bytes_per_second=measurement["bytes_per_second"],
            latency=Latency(**measurement["latency"]),
            first_byte=Latency(**measurement["first_byte"]),
            status_codes=measurement["status_codes"],
            errors=measurement["errors"],
        ),
        usage=ServerUsage(**data["usage"]) if data["usage"] else None,
    )
