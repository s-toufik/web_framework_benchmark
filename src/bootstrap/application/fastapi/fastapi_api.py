from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI
from pycraftcore.web.actuator import Actuator
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web_fastapi import actuator_router, create_app, detail_handler

from bootstrap.application.fastapi.router.shop_router import shop_router
from shop.application.use_case.shop_use_cases import ShopUseCases
from shop.domain.exception.product_not_found import ProductNotFound


def create_fastapi_api(
    api: ApiSettings,
    *,
    lifespan: Callable[[], AbstractAsyncContextManager[None]],
    shop: Callable[[], ShopUseCases],
    actuator: Actuator,
) -> FastAPI:
    return create_app(
        api,
        routes=[shop_router(shop), actuator_router(actuator)],
        lifespan=lifespan,
        exception_handlers={ProductNotFound: detail_handler(404)},
    )
