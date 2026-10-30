from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint import EndpointKind
from shop_benchmark.domain.endpoint_result import EndpointResult
from shop_benchmark.domain.environment import Environment
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.measurement import Latency, Measurement
from shop_benchmark.domain.run_report import RunReport
from shop_benchmark.domain.server_usage import ServerUsage
from shop_benchmark.domain.service import Service

THROUGHPUT = LoadProfile("throughput", 64, 30)
FIXED_RATE = LoadProfile("fixed_rate", 64, 30, 500)


def measurement(rps: float, p99_ms: float, failures: int = 0) -> Measurement:
    latency = Latency(p99_ms / 3, p99_ms / 2, p99_ms / 1.5, p99_ms, p99_ms * 1.2, p99_ms * 2)
    return Measurement(
        requests=1000,
        requests_per_second=rps,
        bytes_per_second=rps * 200,
        latency=latency,
        first_byte=latency,
        status_codes={"200": 1000 - failures, **({"500": failures} if failures else {})},
        errors={},
    )


def result(endpoint: str, profile: LoadProfile, rps: float, p99_ms: float) -> EndpointResult:
    return EndpointResult(
        endpoint=endpoint,
        kind=EndpointKind.JSON,
        method="GET",
        path=f"/v1/{endpoint}",
        profile=profile.name,
        measurement=measurement(rps, p99_ms),
        usage=ServerUsage(80.0, 100.0, 60.0, 64.0, 10),
    )


def report(
    framework: str, numbers: dict[str, tuple[float, float]], fingerprint: str = "abc"
) -> RunReport:
    endpoints = list(numbers)
    return RunReport(
        service=Service("web-framework", "1.0.0", framework, "1.0", "3.14.3", "granian"),
        environment=Environment("host", "Apple M5 Pro", 15, "Darwin 25 (arm64)", "oha 1.16.0"),
        base_url="http://127.0.0.1:8765",
        started_at=f"2026-10-25T10:00:0{len(framework) % 10}+01:00",
        finished_at="2026-10-25T10:10:00+01:00",
        warmup_seconds=5,
        profiles=(THROUGHPUT, FIXED_RATE),
        answers=tuple(
            Answer(endpoint, 200, "application/json", 10, fingerprint) for endpoint in endpoints
        ),
        results=tuple(
            result(endpoint, profile, *numbers[endpoint])
            for profile in (THROUGHPUT, FIXED_RATE)
            for endpoint in endpoints
        ),
    )
