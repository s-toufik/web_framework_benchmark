from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from pycraftcore.web.actuator import Actuator
from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_blacksheep import actuator_router, create_app, detail_handler, openapi_handler
from rodi import Container

from bootstrap.application.blacksheep.router.shop_router import shop_router
from shop.application.use_case.shop_use_cases import ShopUseCases
from shop.domain.exception.product_not_found import ProductNotFound


def create_blacksheep_api(
    api: ApiSettings,
    *,
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
    shop: Callable[[], ShopUseCases],
    actuator: Actuator,
) -> ASGIApp:
    docs = openapi_handler(api)
    services = Container()
    services.add_transient_by_factory(shop, ShopUseCases)
    return create_app(
        api,
        routes=[shop_router(docs), actuator_router(actuator)],
        lifespan=lifespan,
        exception_handlers={ProductNotFound: detail_handler(404)},
        openapi=docs,
        services=services,
    )
