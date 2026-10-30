import hashlib
import json
from pathlib import Path

import pytest

from bootstrap.application.shop_application import (
    create_blacksheep_application,
    create_fastapi_application,
    create_litestar_application,
)
from bootstrap.configuration.settings import ProcessSettings

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"

EVERY_FRAMEWORK = pytest.mark.parametrize(
    "create",
    [create_fastapi_application, create_litestar_application, create_blacksheep_application],
    ids=["fastapi", "litestar", "blacksheep"],
)

ORDER = {
    "customer": "acme",
    "lines": [{"sku": f"SKU-{index:05d}", "quantity": index} for index in range(1, 6)],
}
NOTE = ("The quick brown fox jumps over the lazy dog.\n" * 40).encode()
UPLOAD = hashlib.shake_256(b"upload").digest(65_536)

ENDPOINTS = [
    ("GET", "/v1/products/SKU-00042", None, None, "application/json"),
    ("POST", "/v1/orders", ORDER, None, "application/json"),
    ("GET", "/v1/products/SKU-00042/events", None, None, "text/event-stream"),
    ("POST", "/v1/orders/track", ORDER, None, "text/event-stream"),
    ("GET", "/v1/products/SKU-00042/image", None, None, "application/octet-stream"),
    ("POST", "/v1/files", None, (UPLOAD, "application/octet-stream"), "application/octet-stream"),
    ("GET", "/v1/products/SKU-00042/label", None, None, "text/plain"),
    ("POST", "/v1/notes", None, (NOTE, "text/plain"), "text/plain"),
]


def settings(monkeypatch, tmp_path, docs: bool = False, base_path: str = "") -> ProcessSettings:
    monkeypatch.setenv("SHOP_DB_DIR", str(tmp_path))
    monkeypatch.setenv("WEB_DOCS", str(docs).lower())
    monkeypatch.setenv("WEB_BASE_PATH", base_path)
    return ProcessSettings(role="shop", environment="debug", configuration_directory=CONFIG_DIR)


async def call(client, method, path, payload, raw):
    if raw is not None:
        content, content_type = raw
        return await client.request(
            method, path, content=content, headers={"Content-Type": content_type}
        )
    return await client.request(method, path, json=payload)


def fingerprint(response) -> str:
    body = response.content
    if response.headers["content-type"].startswith("application/json"):
        body = json.dumps(json.loads(body), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()
