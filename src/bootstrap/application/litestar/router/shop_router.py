from typing import Final

from litestar import Controller, MediaType, Response, get, post
from litestar.params import FromPath, JSONBody, RawBody, SkipValidation
from litestar.response import Stream
from pycraftcore.web.sse import EVENT_STREAM_MEDIA_TYPE
from pycraftcore.web_litestar import event_stream

from bootstrap.application.about import About
from bootstrap.application.litestar.schema.order_schema import OrderRequestSchema, OrderSchema
from bootstrap.application.litestar.schema.product_schema import ProductSchema
from bootstrap.application.media_types import BINARY
from shop.adapter.inbound.web.stream.sse_presenter import SsePresenter
from shop.application.use_case.shop_use_cases import ShopUseCases

FRAMEWORK: Final[str] = "litestar"

Shop = SkipValidation[ShopUseCases]


class ShopRouter(Controller):
    path = "/v1"
    tags = ["shop"]

    @get("/products/{sku:str}")
    async def get_product(self, sku: FromPath[str], shop: Shop) -> ProductSchema:
        return ProductSchema.of(await shop.get_product.handle(sku))

    @post("/orders", status_code=200)
    async def place_order(self, data: JSONBody[OrderRequestSchema], shop: Shop) -> OrderSchema:
        return OrderSchema.of(await shop.place_order.handle(data.to_domain()))

    @get("/products/{sku:str}/events", media_type=EVENT_STREAM_MEDIA_TYPE)
    async def follow_product(self, sku: FromPath[str], shop: Shop) -> Stream:
        return event_stream(SsePresenter.ticks(await shop.follow_product.handle(sku)))

    @post("/orders/track", status_code=200, media_type=EVENT_STREAM_MEDIA_TYPE)
    async def track_order(self, data: JSONBody[OrderRequestSchema], shop: Shop) -> Stream:
        events = await shop.track_order.handle(data.to_domain())
        return event_stream(SsePresenter.tracking(events))

    @get("/products/{sku:str}/image", media_type=BINARY)
    async def get_product_image(self, sku: FromPath[str], shop: Shop) -> Response[bytes]:
        return Response(await shop.get_product_image.handle(sku), media_type=BINARY)

    @post("/files", status_code=200, media_type=BINARY)
    async def store_file(self, body: RawBody, shop: Shop) -> Response[bytes]:
        return Response((await shop.store_file.handle(body)).digest, media_type=BINARY)

    @get("/products/{sku:str}/label", media_type=MediaType.TEXT)
    async def render_label(self, sku: FromPath[str], shop: Shop) -> str:
        return (await shop.render_label.handle(sku)).text

    @post("/notes", status_code=200, media_type=MediaType.TEXT)
    async def save_note(self, body: RawBody, shop: Shop) -> str:
        return (await shop.save_note.handle(body.decode())).summary

    @get("/about")
    async def about(self) -> About:
        return About.of(FRAMEWORK)
