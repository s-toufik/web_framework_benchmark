import json
from pathlib import Path

from shop_benchmark.adapter.oha.oha_load_generator import OhaLoadGenerator
from shop_benchmark.adapter.oha.oha_output import measurement_of
from shop_benchmark.domain.endpoint import Endpoint, EndpointKind
from shop_benchmark.domain.load_profile import LoadProfile

OUTPUT = json.loads((Path(__file__).parent / "fixtures" / "oha_output.json").read_text())


def test_oha_output_becomes_a_measurement_in_milliseconds() -> None:
    measurement = measurement_of(OUTPUT)

    assert measurement.requests == 1972
    assert round(measurement.requests_per_second) == 986
    assert round(measurement.latency.p50_ms, 3) == 8.052
    assert round(measurement.latency.p99_ms, 3) == 9.937
    assert round(measurement.first_byte.mean_ms, 3) == 8.081
    assert measurement.status_codes == {"200": 1972}


def test_a_throughput_profile_runs_for_its_duration_on_its_connections(tmp_path) -> None:
    endpoint = Endpoint(
        "get_json", EndpointKind.JSON, "GET", "/v1/products/SKU-00042", "application/json"
    )

    command = OhaLoadGenerator("http://127.0.0.1:8765/").command(
        endpoint, LoadProfile("throughput", 64, 30), 2.5, tmp_path
    )

    assert command[:5] == [
        "oha",
        "--no-tui",
        "--output-format",
        "json",
        "--wait-ongoing-requests-after-deadline",
    ]
    assert command[5:11] == ["-z", "2500ms", "-c", "64", "-m", "GET"]
    assert "-q" not in command
    assert command[-1] == "http://127.0.0.1:8765/v1/products/SKU-00042"


def test_a_fixed_rate_profile_with_a_body_sends_it_from_a_file(tmp_path) -> None:
    endpoint = Endpoint(
        "post_binary",
        EndpointKind.BINARY,
        "POST",
        "/v1/files",
        "application/octet-stream",
        b"\x00\x01",
        "application/octet-stream",
    )

    command = OhaLoadGenerator("http://127.0.0.1:8765").command(
        endpoint, LoadProfile("fixed_rate", 64, 30, 500), 30, tmp_path
    )

    assert command[command.index("-q") : command.index("-q") + 3] == [
        "-q",
        "500",
        "--latency-correction",
    ]
    assert command[command.index("-T") + 1] == "application/octet-stream"
    assert Path(command[command.index("-D") + 1]).read_bytes() == b"\x00\x01"
