from typing import Final

from blacksheep import Content, Request, Response, Router, text
from blacksheep.server.bindings import FromBytes, FromText
from blacksheep.server.openapi.common import ContentInfo, ResponseInfo
from blacksheep.server.openapi.v3 import OpenAPIHandler
from pycraftcore.web.sse import EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web_blacksheep import event_stream

from bootstrap.application.about import About
from bootstrap.application.blacksheep.schema.order_schema import OrderRequestSchema, OrderSchema
from bootstrap.application.blacksheep.schema.product_schema import ProductSchema
from bootstrap.application.media_types import BINARY, TEXT
from shop.adapter.inbound.web.stream.sse_presenter import SsePresenter
from shop.application.use_case.shop_use_cases import ShopUseCases

FRAMEWORK: Final[str] = "blacksheep"
TAGS: Final[list[str]] = ["shop"]
EVENT_STREAM: Final[ResponseInfo] = ResponseInfo(
    "Event stream", content=[ContentInfo(str, content_type=EVENT_STREAM_MEDIA_TYPE)]
)
BINARY_RESPONSE: Final[ResponseInfo] = ResponseInfo(
    "Binary content", content=[ContentInfo(bytes, content_type=BINARY)]
)
TEXT_RESPONSE: Final[ResponseInfo] = ResponseInfo(
    "Plain text", content=[ContentInfo(str, content_type=TEXT)]
)


def shop_router(docs: OpenAPIHandler) -> Router:
    router = Router(prefix="/v1")

    @docs(tags=TAGS)
    @router.get("/products/{sku}")
    async def get_product(sku: str, shop: ShopUseCases) -> ProductSchema:
        return ProductSchema.of(await shop.get_product.handle(sku))

    @docs(tags=TAGS)
    @router.post("/orders")
    async def place_order(order: OrderRequestSchema, shop: ShopUseCases) -> OrderSchema:
        return OrderSchema.of(await shop.place_order.handle(order.to_domain()))

    @docs(tags=TAGS, responses={200: EVENT_STREAM})
    @router.get("/products/{sku}/events")
    async def follow_product(request: Request, sku: str, shop: ShopUseCases) -> Response:
        ticks = await shop.follow_product.handle(sku)
        return event_stream(SsePresenter.ticks(ticks), request)

    @docs(tags=TAGS, responses={200: EVENT_STREAM})
    @router.post("/orders/track")
    async def track_order(
        request: Request, order: OrderRequestSchema, shop: ShopUseCases
    ) -> Response:
        events = await shop.track_order.handle(order.to_domain())
        return event_stream(SsePresenter.tracking(events), request)

    @docs(tags=TAGS, responses={200: BINARY_RESPONSE})
    @router.get("/products/{sku}/image")
    async def get_product_image(sku: str, shop: ShopUseCases) -> Response:
        image = await shop.get_product_image.handle(sku)
        return Response(200, content=Content(BINARY.encode(), image))

    @docs(tags=TAGS, responses={200: BINARY_RESPONSE})
    @router.post("/files")
    async def store_file(content: FromBytes, shop: ShopUseCases) -> Response:
        stored = await shop.store_file.handle(content.value)
        return Response(200, content=Content(BINARY.encode(), stored.digest))

    @docs(tags=TAGS, responses={200: TEXT_RESPONSE})
    @router.get("/products/{sku}/label")
    async def render_label(sku: str, shop: ShopUseCases) -> Response:
        return text((await shop.render_label.handle(sku)).text)

    @docs(tags=TAGS, responses={200: TEXT_RESPONSE})
    @router.post("/notes")
    async def save_note(note: FromText, shop: ShopUseCases) -> Response:
        return text((await shop.save_note.handle(note.value)).summary)

    @docs(tags=TAGS)
    @router.get("/about")
    async def about() -> About:
        return About.of(FRAMEWORK)

    return router
