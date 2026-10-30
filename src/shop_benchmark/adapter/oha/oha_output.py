from collections.abc import Mapping
from typing import Any

from shop_benchmark.domain.measurement import Latency, Measurement

MILLISECONDS: float = 1_000


def measurement_of(output: Mapping[str, Any]) -> Measurement:
    summary = output["summary"]
    first_byte = output["details"]["firstByte"]
    status_codes = {
        str(status): int(count) for status, count in output["statusCodeDistribution"].items()
    }
    return Measurement(
        requests=sum(status_codes.values()),
        requests_per_second=float(summary["requestsPerSec"] or 0.0),
        bytes_per_second=float(summary["sizePerSec"] or 0.0),
        latency=_latency(output["latencyPercentiles"], summary["average"], summary["slowest"]),
        first_byte=_latency(
            output["firstBytePercentiles"], first_byte["average"], first_byte["slowest"]
        ),
        status_codes=status_codes,
        errors={str(error): int(count) for error, count in output["errorDistribution"].items()},
    )


def _latency(percentiles: Mapping[str, Any], average: Any, slowest: Any) -> Latency:
    return Latency(
        mean_ms=_ms(average),
        p50_ms=_ms(percentiles.get("p50")),
        p90_ms=_ms(percentiles.get("p90")),
        p99_ms=_ms(percentiles.get("p99")),
        p999_ms=_ms(percentiles.get("p99.9")),
        max_ms=_ms(slowest),
    )


def _ms(seconds: Any) -> float:
    return float(seconds or 0.0) * MILLISECONDS
