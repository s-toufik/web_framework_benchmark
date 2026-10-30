import pytest

from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.comparison import Comparison
from shop_benchmark.domain.endpoint import Endpoint, EndpointKind
from shop_benchmark.domain.server_usage import ServerUsage
from shop_benchmark.workload.catalog import Workload
from tests.shop_benchmark.builders import measurement, report

WORKLOAD = Workload("SKU-00042", 5, 1024, 3)


def test_the_workload_covers_every_method_and_kind_with_the_same_bodies() -> None:
    endpoints = WORKLOAD.endpoints()

    assert [endpoint.name for endpoint in endpoints] == [
        "get_json",
        "post_json",
        "get_stream",
        "post_stream",
        "get_binary",
        "post_binary",
        "get_text",
        "post_text",
    ]
    assert endpoints == Workload("SKU-00042", 5, 1024, 3).endpoints()
    assert len(endpoints[5].body or b"") == 1024


def test_an_answer_reports_every_problem() -> None:
    endpoint = Endpoint("get_text", EndpointKind.TEXT, "GET", "/v1/x", "text/plain")

    assert Answer("get_text", 200, "text/plain; charset=utf-8", 10, "f").problems(endpoint) == []
    assert len(Answer("get_text", 500, "application/json", 0, "f").problems(endpoint)) == 3


def test_failures_count_non_2xx_answers_and_transport_errors() -> None:
    assert measurement(100, 5, failures=3).failures == 3
    assert measurement(100, 5).error_rate == 0


def test_server_usage_is_none_without_samples() -> None:
    assert ServerUsage.of([]) is None
    assert ServerUsage.of([(50.0, 10.0), (150.0, 30.0)]) == ServerUsage(100.0, 150.0, 20.0, 30.0, 2)


def test_throughput_is_ranked_by_requests_and_fixed_rate_by_p99() -> None:
    comparison = Comparison.of(
        [
            report("fastapi", {"get_json": (1000, 9.0)}),
            report("litestar", {"get_json": (2000, 6.0)}),
            report("blacksheep", {"get_json": (1500, 3.0)}),
        ]
    )

    throughput, fixed_rate = comparison.matchups
    assert [standing.framework for standing in throughput.standings] == [
        "litestar",
        "blacksheep",
        "fastapi",
    ]
    assert [standing.framework for standing in fixed_rate.standings] == [
        "blacksheep",
        "litestar",
        "fastapi",
    ]
    assert throughput.standing("fastapi").ratio == pytest.approx(0.5)
    assert fixed_rate.standing("fastapi").ratio == pytest.approx(1 / 3)


def test_a_framework_best_everywhere_scores_100() -> None:
    comparison = Comparison.of(
        [
            report("fastapi", {"get_json": (1000, 9.0), "get_text": (1000, 9.0)}),
            report("litestar", {"get_json": (4000, 3.0), "get_text": (2000, 3.0)}),
        ]
    )

    scores = {score.framework: score for score in comparison.scores("throughput")}
    assert scores["litestar"].score == 100.0
    assert scores["litestar"].wins == 2
    assert scores["fastapi"].score == pytest.approx(100 * (0.25 * 0.5) ** 0.5, abs=0.1)


def test_answers_that_differ_between_frameworks_are_flagged() -> None:
    comparison = Comparison.of(
        [
            report("fastapi", {"get_json": (1, 1)}, "abc"),
            report("litestar", {"get_json": (1, 1)}, "xyz"),
        ]
    )

    assert comparison.mismatched_answers() == ["get_json"]
