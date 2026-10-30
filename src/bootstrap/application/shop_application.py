import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Final

from pycraftcore.web.asgi import ASGIApp
from pycraftcore.web.schema import ApiSettings

from bootstrap.application.blacksheep.blacksheep_api import create_blacksheep_api
from bootstrap.application.fastapi.fastapi_api import create_fastapi_api
from bootstrap.application.litestar.litestar_api import create_litestar_api
from bootstrap.configuration.settings import ProcessSettings
from bootstrap.container.shop_container import ShopContainer
from src import APPLICATION_VERSION

ROLE: Final[str] = "shop"


@asynccontextmanager
async def _lifespan(container: ShopContainer) -> AsyncGenerator[None]:
    try:
        await container.boot()
    except Exception as exception:
        container.logging.critical(
            "Shop container failed to boot:\n" + "".join(traceback.format_exception(exception))
        )
        raise

    try:
        yield
    finally:
        await container.stop()


def _container(settings: ProcessSettings | None) -> ShopContainer:
    return ShopContainer(settings or ProcessSettings.for_role(ROLE))


def _api(container: ShopContainer) -> ApiSettings:
    server = container.server
    return ApiSettings(
        title=server.name,
        version=APPLICATION_VERSION,
        base_path=server.base_path,
        docs=server.docs,
        cors_origins=server.cors_origins,
    )


def create_fastapi_application(settings: ProcessSettings | None = None) -> ASGIApp:
    container = _container(settings)
    return create_fastapi_api(
        _api(container),
        lifespan=lambda: _lifespan(container),
        shop=lambda: container.use_cases,
        actuator=container.actuator,
    )


def create_litestar_application(settings: ProcessSettings | None = None) -> ASGIApp:
    container = _container(settings)
    return create_litestar_api(
        _api(container),
        lifespan=lambda: _lifespan(container),
        shop=lambda: container.use_cases,
        actuator=container.actuator,
    )


def create_blacksheep_application(settings: ProcessSettings | None = None) -> ASGIApp:
    container = _container(settings)
    return create_blacksheep_api(
        _api(container),
        lifespan=lambda: _lifespan(container),
        shop=lambda: container.use_cases,
        actuator=container.actuator,
    )
