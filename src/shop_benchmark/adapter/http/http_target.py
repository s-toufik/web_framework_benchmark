import hashlib
import json

import httpx

from shop_benchmark.domain.answer import Answer
from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.service import Service

ABOUT_PATH: str = "/v1/about"


class HttpTarget:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def about(self) -> Service:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}{ABOUT_PATH}")
        response.raise_for_status()
        about = response.json()
        return Service(
            name=about["service"],
            version=about["version"],
            framework=about["framework"],
            framework_version=about["framework_version"],
            python=about["python"],
            server=about["server"],
        )

    async def call(self, endpoint: Endpoint) -> Answer:
        headers = {"Content-Type": endpoint.content_type} if endpoint.content_type else {}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(
                endpoint.method,
                f"{self._base_url}{endpoint.path}",
                content=endpoint.body,
                headers=headers,
            )
        media_type = response.headers.get("content-type", "")
        return Answer(
            endpoint=endpoint.name,
            status=response.status_code,
            media_type=media_type,
            size=len(response.content),
            fingerprint=_fingerprint(response.content, media_type),
        )


def _fingerprint(body: bytes, media_type: str) -> str:
    if media_type.startswith("application/json"):
        body = json.dumps(json.loads(body), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()[:16]
