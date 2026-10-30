import hashlib
import json
from dataclasses import dataclass

from shop_benchmark.domain.endpoint import Endpoint, EndpointKind

JSON = "application/json"
EVENT_STREAM = "text/event-stream"
BINARY = "application/octet-stream"
TEXT = "text/plain"
NOTE_LINE = "The quick brown fox jumps over the lazy dog while the shop keeps counting words.\n"


@dataclass(frozen=True, slots=True)
class Workload:
    sku: str
    order_lines: int
    upload_bytes: int
    note_lines: int

    def endpoints(self) -> tuple[Endpoint, ...]:
        order = self._order()
        product = f"/v1/products/{self.sku}"
        return (
            Endpoint("get_json", EndpointKind.JSON, "GET", product, JSON),
            Endpoint("post_json", EndpointKind.JSON, "POST", "/v1/orders", JSON, order, JSON),
            Endpoint("get_stream", EndpointKind.STREAM, "GET", f"{product}/events", EVENT_STREAM),
            Endpoint(
                "post_stream",
                EndpointKind.STREAM,
                "POST",
                "/v1/orders/track",
                EVENT_STREAM,
                order,
                JSON,
            ),
            Endpoint("get_binary", EndpointKind.BINARY, "GET", f"{product}/image", BINARY),
            Endpoint(
                "post_binary",
                EndpointKind.BINARY,
                "POST",
                "/v1/files",
                BINARY,
                self._upload(),
                BINARY,
            ),
            Endpoint("get_text", EndpointKind.TEXT, "GET", f"{product}/label", TEXT),
            Endpoint("post_text", EndpointKind.TEXT, "POST", "/v1/notes", TEXT, self._note(), TEXT),
        )

    def _order(self) -> bytes:
        lines = [
            {"sku": f"SKU-{index:05d}", "quantity": index}
            for index in range(1, self.order_lines + 1)
        ]
        return json.dumps({"customer": "benchmark", "lines": lines}, separators=(",", ":")).encode()

    def _upload(self) -> bytes:
        return hashlib.shake_256(b"shop benchmark upload").digest(self.upload_bytes)

    def _note(self) -> bytes:
        return (NOTE_LINE * self.note_lines).encode()
