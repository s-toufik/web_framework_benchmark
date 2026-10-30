from shop_benchmark.adapter.report.formatting import megabytes_per_second, ms, percent, rate, table
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.run_report import RunReport


def render_run(report: RunReport) -> str:
    service, environment = report.service, report.environment
    lines = [
        f"# Benchmark: {service.title}",
        "",
        *table(
            ["", ""],
            ["left", "left"],
            [
                ["Service", f"{service.name} {service.version}"],
                ["Framework", service.title],
                ["Server", f"{service.server}, Python {service.python}"],
                ["Target", report.base_url],
                ["Run", f"{report.started_at} → {report.finished_at}"],
                ["Machine", f"{environment.cpu}, {environment.cores} cores, {environment.system}"],
                ["Load generator", environment.load_generator],
                ["Warm-up", f"{report.warmup_seconds:g} s before each measured run"],
            ],
        ),
    ]
    for profile in report.profiles:
        results = report.results_for(profile.name)
        lines += ["", f"## {profile.name}: {profile.description}", ""]
        lines += table(
            [
                "Endpoint",
                "Path",
                "Requests/s",
                "p50 ms",
                "p90 ms",
                "p99 ms",
                "Max ms",
                "First byte p50 ms",
                "MB/s",
                "Failures",
                "Server CPU % mean / max",
                "Server memory MB max",
            ],
            ["left", "left", *["right"] * 10],
            [_row(result) for result in results],
        )
    lines += ["", "## Preflight answers", ""]
    lines += table(
        ["Endpoint", "Status", "Media type", "Bytes", "Fingerprint"],
        ["left", "right", "left", "right", "left"],
        [
            [
                answer.endpoint,
                str(answer.status),
                answer.media_type,
                rate(answer.size),
                f"`{answer.fingerprint}`",
            ]
            for answer in report.answers
        ],
    )
    lines += ["", *READING_GUIDE]
    return "\n".join(lines) + "\n"


def _row(result: EndpointResult) -> list[str]:
    measurement, usage = result.measurement, result.usage
    latency = measurement.latency
    return [
        result.label,
        f"`{result.method} {result.path}`",
        rate(measurement.requests_per_second),
        ms(latency.p50_ms),
        ms(latency.p90_ms),
        ms(latency.p99_ms),
        ms(latency.max_ms),
        ms(measurement.first_byte.p50_ms),
        megabytes_per_second(measurement.bytes_per_second),
        str(measurement.failures),
        f"{percent(usage.cpu_percent_mean)} / {percent(usage.cpu_percent_max)}" if usage else "—",
        f"{usage.memory_mb_max:.0f}" if usage else "—",
    ]


READING_GUIDE = [
    "## Reading this report",
    "",
    "- **Requests/s** is the throughput oha sustained; under a fixed-rate profile it should equal the target rate, and less means the server fell behind.",
    "- **p50 / p90 / p99** are latency percentiles: half, 90 % and 99 % of requests were faster. Fixed-rate profiles correct latency for requests that had to wait, so a slow server cannot hide it.",
    "- **First byte** is when the first byte of the answer arrived: for streams, the time to the first event.",
    "- **Failures** counts non-2xx answers and transport errors; any value above 0 makes the row unreliable.",
    "- **Server CPU** is summed over the server's processes: 100 % is one full core. **Memory** is their resident memory.",
    "- The load generator runs on the same machine as the server and takes CPU too: compare frameworks run on the same machine only.",
]
