from collections.abc import Callable

from shop_benchmark.adapter.report.formatting import fewer, ms, percent, rate, slower, table
from shop_benchmark.domain.comparison import Comparison, Matchup
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.load_profile import LoadProfile


def render_comparison(comparison: Comparison, generated_at: str) -> str:
    frameworks = comparison.frameworks
    first = comparison.reports[0]
    lines = [
        f"# Framework comparison: {', '.join(frameworks)}",
        "",
        f"Generated {generated_at}. Each framework served the same shop, with the same data, on the same machine, under the same load; only the web framework changes.",
        "",
        *table(
            ["Framework", "Server", "Measured"],
            ["left", "left", "left"],
            [
                [
                    report.service.title,
                    f"{report.service.server}, Python {report.service.python}",
                    report.started_at,
                ]
                for report in comparison.reports
            ],
        ),
        "",
        f"Machine: {first.environment.cpu}, {first.environment.cores} cores, {first.environment.system}. "
        f"Load generator: {first.environment.load_generator}. Warm-up: {first.warmup_seconds:g} s before each run.",
        "",
        "## Summary",
        "",
    ]
    lines += table(
        [
            "Framework",
            *(f"{profile.name} score" for profile in comparison.profiles),
            *(f"{profile.name} wins" for profile in comparison.profiles),
            "Peak memory MB",
        ],
        ["left", *["right"] * (2 * len(comparison.profiles) + 1)],
        _summary_rows(comparison),
    )
    lines += [
        "",
        "A score of 100 means best on every endpoint. It is the geometric mean, over the endpoints, of each framework's ratio to the best: requests per second for throughput profiles, p99 latency for fixed-rate profiles.",
        "",
        "## Same work everywhere",
        "",
    ]
    mismatched = comparison.mismatched_answers()
    lines.append(
        "Every endpoint returned the same bytes on every framework, so every framework did the same work."
        if not mismatched
        else "⚠️ These endpoints answered differently between frameworks, so their numbers are not comparable: "
        + ", ".join(mismatched)
    )
    for profile in comparison.profiles:
        lines += _profile_section(comparison, profile)
    lines += _resources_section(comparison)
    lines += ["", *READING_GUIDE]
    return "\n".join(lines) + "\n"


def _summary_rows(comparison: Comparison) -> list[list[str]]:
    scores = {
        profile.name: {score.framework: score for score in comparison.scores(profile.name)}
        for profile in comparison.profiles
    }
    rows = []
    for report in comparison.reports:
        framework = report.framework
        peak = max(
            (result.usage.memory_mb_max for result in report.results if result.usage), default=None
        )
        rows.append(
            [
                report.service.title,
                *(
                    f"{scores[profile.name][framework].score:.1f}"
                    for profile in comparison.profiles
                ),
                *(str(scores[profile.name][framework].wins) for profile in comparison.profiles),
                f"{peak:.0f}" if peak is not None else "—",
            ]
        )
    return rows


def _profile_section(comparison: Comparison, profile: LoadProfile) -> list[str]:
    matchups = comparison.matchups_for(profile.name)
    frameworks = comparison.frameworks
    lines = ["", f"## {profile.name}: {profile.description}", ""]
    if profile.is_fixed_rate:
        lines += ["### p99 latency, ms (lower is better)", ""]
        lines += _matchup_table(
            frameworks, matchups, lambda result: ms(result.measurement.latency.p99_ms), slower
        )
        lines += ["", "### p50 latency, ms", ""]
        lines += _value_table(
            frameworks, matchups, lambda result: ms(result.measurement.latency.p50_ms)
        )
        lines += [
            "",
            f"### Requests per second achieved (target {profile.rate_per_second}) and failures",
            "",
        ]
        lines += _value_table(
            frameworks,
            matchups,
            lambda result: (
                f"{rate(result.measurement.requests_per_second)} / {result.measurement.failures}"
            ),
        )
    else:
        lines += ["### Requests per second (higher is better)", ""]
        lines += _matchup_table(
            frameworks, matchups, lambda result: rate(result.measurement.requests_per_second), fewer
        )
        lines += ["", "### p99 latency at that throughput, ms", ""]
        lines += _value_table(
            frameworks, matchups, lambda result: ms(result.measurement.latency.p99_ms)
        )
        lines += ["", "### Failures", ""]
        lines += _value_table(frameworks, matchups, lambda result: str(result.measurement.failures))
    return lines


def _matchup_table(
    frameworks: list[str],
    matchups: list[Matchup],
    value: Callable[[EndpointResult], str],
    behind: Callable[[float], str],
) -> list[str]:
    rows = []
    for matchup in matchups:
        cells = []
        for framework in frameworks:
            standing = matchup.standing(framework)
            if standing is None:
                cells.append("—")
            elif framework == matchup.winner:
                cells.append(f"**{value(standing.result)}**")
            else:
                cells.append(value(standing.result) + behind(standing.ratio))
        rows.append([matchup.label, *cells, matchup.winner])
    return table(
        ["Endpoint", *frameworks, "Best"], ["left", *["right"] * len(frameworks), "left"], rows
    )


def _value_table(
    frameworks: list[str], matchups: list[Matchup], value: Callable[[EndpointResult], str]
) -> list[str]:
    rows = []
    for matchup in matchups:
        cells = []
        for framework in frameworks:
            standing = matchup.standing(framework)
            cells.append(value(standing.result) if standing else "—")
        rows.append([matchup.label, *cells])
    return table(["Endpoint", *frameworks], ["left", *["right"] * len(frameworks)], rows)


def _resources_section(comparison: Comparison) -> list[str]:
    rows = []
    for report in comparison.reports:
        for profile in comparison.profiles:
            usages = [result.usage for result in report.results_for(profile.name) if result.usage]
            if not usages:
                rows.append([report.service.title, profile.name, "—", "—", "—"])
                continue
            rows.append(
                [
                    report.service.title,
                    profile.name,
                    percent(sum(usage.cpu_percent_mean for usage in usages) / len(usages)),
                    percent(max(usage.cpu_percent_max for usage in usages)),
                    f"{max(usage.memory_mb_max for usage in usages):.0f}",
                ]
            )
    return [
        "",
        "## Server resources",
        "",
        *table(
            ["Framework", "Profile", "CPU % mean", "CPU % max", "Memory MB max"],
            ["left", "left", "right", "right", "right"],
            rows,
        ),
    ]


READING_GUIDE = [
    "## How to read this comparison",
    "",
    "- **Throughput profiles** push as many requests as the connections allow: the best framework serves the most requests per second. Bold is the best; the percentage is how many fewer requests the others served.",
    "- **Fixed-rate profiles** send the same number of requests per second to every framework: the best framework answers with the lowest p99 latency, and the percentage is how much slower the others are. If a framework achieved less than the target rate, it could not keep up.",
    "- **Differences under about 5 % are within run-to-run noise**: run the benchmark several times before drawing a conclusion from them.",
    "- **Any failure** makes that framework's row for the endpoint unreliable.",
    "- The numbers belong to this machine and this shop's work (database, fake APIs with fixed latency, streams paced by a fake feed); a different workload can rank the frameworks differently.",
]
