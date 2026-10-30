from pathlib import Path

import pytest

from shop_benchmark.adapter.probe.process_probe import NoProbe, ProcessProbe
from shop_benchmark.bootstrap.container import BenchmarkContainer, UnknownEndpoints
from shop_benchmark.configuration.control_panel import ControlPanel, Overrides

PANEL = Path(__file__).resolve().parents[2] / "src" / "shop_benchmark" / "control_panel.json"


def test_the_shipped_control_panel_loads_with_two_profiles() -> None:
    panel = ControlPanel.load_file(PANEL)

    assert [profile.name for profile in panel.load.profiles] == ["throughput", "fixed_rate"]
    assert panel.load.profiles[1].rate_per_second == 500


def test_overrides_shorten_every_profile_and_pick_endpoints_and_profiles() -> None:
    panel = Overrides(
        duration_seconds=3, warmup_seconds=1, endpoints=["get_json"], profiles=["throughput"]
    ).apply(ControlPanel.load_file(PANEL))

    plan = BenchmarkContainer(panel).plan
    assert [endpoint.name for endpoint in plan.endpoints] == ["get_json"]
    assert [(profile.name, profile.duration_seconds) for profile in plan.profiles] == [
        ("throughput", 3)
    ]
    assert plan.warmup_seconds == 1


def test_an_unknown_endpoint_is_refused() -> None:
    panel = Overrides(endpoints=["get_xml"]).apply(ControlPanel.load_file(PANEL))

    with pytest.raises(UnknownEndpoints, match="get_xml"):
        _ = BenchmarkContainer(panel).plan


@pytest.mark.parametrize(
    ("base_url", "probe"),
    [("http://127.0.0.1:8765", ProcessProbe), ("http://shop.example.com:8765", NoProbe)],
)
def test_the_server_is_probed_only_when_it_runs_on_this_machine(base_url, probe) -> None:
    panel = Overrides(base_url=base_url).apply(ControlPanel.load_file(PANEL))

    assert isinstance(BenchmarkContainer(panel)._probe(), probe)


async def test_a_probe_without_a_listening_server_measures_nothing() -> None:
    async def work() -> str:
        return "done"

    assert await ProcessProbe(port=1, interval_seconds=0.01).during(work()) == ("done", None)
