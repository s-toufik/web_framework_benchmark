from collections.abc import Callable
from typing import Annotated, Any, Final

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, Response
from pycraftcore.web_fastapi import EventStreamResponse, event_stream

from bootstrap.application.about import About
from bootstrap.application.fastapi.schema.order_schema import OrderRequestSchema, OrderSchema
from bootstrap.application.fastapi.schema.product_schema import ProductSchema
from bootstrap.application.media_types import BINARY, TEXT
from shop.adapter.inbound.web.stream.sse_presenter import SsePresenter
from shop.application.use_case.shop_use_cases import ShopUseCases

FRAMEWORK: Final[str] = "fastapi"
BINARY_CONTENT: Final[dict[str, Any]] = {BINARY: {"schema": {"type": "string", "format": "binary"}}}
TEXT_CONTENT: Final[dict[str, Any]] = {TEXT: {"schema": {"type": "string"}}}


def shop_router(shop: Callable[[], ShopUseCases]) -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["shop"])
    Shop = Annotated[ShopUseCases, Depends(shop)]

    @router.get("/products/{sku}")
    async def get_product(sku: str, use_cases: Shop) -> ProductSchema:
        return ProductSchema.of(await use_cases.get_product.handle(sku))

    @router.post("/orders")
    async def place_order(order: OrderRequestSchema, use_cases: Shop) -> OrderSchema:
        return OrderSchema.of(await use_cases.place_order.handle(order.to_domain()))

    @router.get("/products/{sku}/events", response_class=EventStreamResponse)
    async def follow_product(sku: str, use_cases: Shop) -> EventStreamResponse:
        return event_stream(SsePresenter.ticks(await use_cases.follow_product.handle(sku)))

    @router.post("/orders/track", response_class=EventStreamResponse)
    async def track_order(order: OrderRequestSchema, use_cases: Shop) -> EventStreamResponse:
        events = await use_cases.track_order.handle(order.to_domain())
        return event_stream(SsePresenter.tracking(events))

    @router.get(
        "/products/{sku}/image",
        response_class=Response,
        responses={200: {"content": BINARY_CONTENT}},
    )
    async def get_product_image(sku: str, use_cases: Shop) -> Response:
        return Response(await use_cases.get_product_image.handle(sku), media_type=BINARY)

    @router.post(
        "/files",
        response_class=Response,
        responses={200: {"content": BINARY_CONTENT}},
        openapi_extra={"requestBody": {"content": BINARY_CONTENT, "required": True}},
    )
    async def store_file(request: Request, use_cases: Shop) -> Response:
        stored = await use_cases.store_file.handle(await request.body())
        return Response(stored.digest, media_type=BINARY)

    @router.get("/products/{sku}/label", response_class=PlainTextResponse)
    async def render_label(sku: str, use_cases: Shop) -> PlainTextResponse:
        return PlainTextResponse((await use_cases.render_label.handle(sku)).text)

    @router.post(
        "/notes",
        response_class=PlainTextResponse,
        openapi_extra={"requestBody": {"content": TEXT_CONTENT, "required": True}},
    )
    async def save_note(request: Request, use_cases: Shop) -> PlainTextResponse:
        note = await use_cases.save_note.handle((await request.body()).decode())
        return PlainTextResponse(note.summary)

    @router.get("/about")
    async def about() -> About:
        return About.of(FRAMEWORK)

    return router
