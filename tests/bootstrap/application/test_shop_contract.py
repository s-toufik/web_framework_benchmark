import pytest

from bootstrap.application.shop_application import (
    create_blacksheep_application,
    create_fastapi_application,
    create_litestar_application,
)
from tests.bootstrap.application.support import (
    ENDPOINTS,
    EVERY_FRAMEWORK,
    call,
    fingerprint,
    settings,
)
from tests.support.web import http_client


@EVERY_FRAMEWORK
@pytest.mark.parametrize(("method", "path", "payload", "raw", "media_type"), ENDPOINTS)
async def test_each_endpoint_answers_with_its_media_type(
    create, monkeypatch, tmp_path, method, path, payload, raw, media_type
) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        response = await call(client, method, path, payload, raw)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media_type)
    assert response.content


async def test_every_framework_answers_every_endpoint_with_the_same_bytes(
    monkeypatch, tmp_path
) -> None:
    answers = []
    for create in (
        create_fastapi_application,
        create_litestar_application,
        create_blacksheep_application,
    ):
        async with http_client(create(settings(monkeypatch, tmp_path))) as client:
            answers.append(
                [
                    fingerprint(await call(client, method, path, payload, raw))
                    for method, path, payload, raw, _ in ENDPOINTS
                ]
            )

    assert answers[0] == answers[1] == answers[2]


@EVERY_FRAMEWORK
async def test_streams_end_with_an_end_frame_counting_their_events(
    create, monkeypatch, tmp_path
) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        ticks = (await client.get("/v1/products/SKU-00042/events")).text
        tracking = (await call(client, *ENDPOINTS[3][:4])).text

    assert ticks.count("event: tick\n") == 20
    assert ticks.endswith('event: end\ndata: {"events":20}\n\n')
    assert tracking.count("event: tracking\n") == 5


@EVERY_FRAMEWORK
async def test_an_unknown_product_is_a_404_with_a_detail(create, monkeypatch, tmp_path) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        product = await client.get("/v1/products/SKU-99999")
        tracked = await client.post(
            "/v1/orders/track",
            json={"customer": "acme", "lines": [{"sku": "SKU-99999", "quantity": 1}]},
        )

    assert (product.status_code, product.json()) == (404, {"detail": "No product 'SKU-99999'"})
    assert tracked.status_code == 404


@EVERY_FRAMEWORK
async def test_an_invalid_order_is_a_client_error(create, monkeypatch, tmp_path) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        response = await client.post("/v1/orders", json={"customer": "", "lines": []})

    assert response.status_code in (400, 422)


@EVERY_FRAMEWORK
async def test_about_names_the_framework_that_answers(create, monkeypatch, tmp_path) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        about = (await client.get("/v1/about")).json()

    assert create.__name__ == f"create_{about['framework']}_application"
    assert about["service"] == "web-framework"


@EVERY_FRAMEWORK
async def test_the_shop_is_ready_once_booted(create, monkeypatch, tmp_path) -> None:
    async with http_client(create(settings(monkeypatch, tmp_path))) as client:
        response = await client.get("/actuator/health/readiness")

    assert (response.status_code, response.json()) == (200, {"status": "UP"})


@EVERY_FRAMEWORK
async def test_the_documentation_lists_every_endpoint_under_the_base_path(
    create, monkeypatch, tmp_path
) -> None:
    app = create(settings(monkeypatch, tmp_path, docs=True, base_path="/shop"))
    async with http_client(app) as client:
        paths = set((await client.get("/shop/docs/openapi.json")).json()["paths"])

    assert {
        "/shop/v1/products/{sku}",
        "/shop/v1/orders",
        "/shop/v1/products/{sku}/events",
        "/shop/v1/orders/track",
        "/shop/v1/products/{sku}/image",
        "/shop/v1/files",
        "/shop/v1/products/{sku}/label",
        "/shop/v1/notes",
    } <= paths
