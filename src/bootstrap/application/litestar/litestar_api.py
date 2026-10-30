from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from litestar import Litestar
from litestar.di import Provide
from pycraftcore.web.actuator import Actuator
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_litestar import actuator_router, create_app, detail_handler

from bootstrap.application.litestar.router.shop_router import ShopRouter
from shop.application.use_case.shop_use_cases import ShopUseCases
from shop.domain.exception.product_not_found import ProductNotFound


def create_litestar_api(
    api: ApiSettings,
    *,
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
    shop: Callable[[], ShopUseCases],
    actuator: Actuator,
) -> Litestar:
    return create_app(
        api,
        routes=[ShopRouter, actuator_router(actuator)],
        lifespan=lifespan,
        exception_handlers={ProductNotFound: detail_handler(404)},
        dependencies={"shop": Provide(shop, sync_to_thread=False)},
    )
