from functools import cached_property

from pycraftcore.application_configuration import ApplicationConfiguration
from pycraftcore.application_configuration.model.server import AsgiServer
from pycraftcore.logger.port import Logger
from pycraftcore.web.actuator import Actuator

from bootstrap.di.shop_di import ShopDI
from shop.adapter.outbound.sqlite.shop_schema import reset_schema
from shop.application.use_case.shop_use_cases import ShopUseCases
from src import (
    APPLICATION_AUTHORS_EMAIL,
    APPLICATION_DEPLOYMENT_ENVIRONMENT,
    APPLICATION_NAME,
    APPLICATION_VERSION,
)


class ShopContainer(ShopDI):
    _ready: bool = False
    _use_cases_after_boot: ShopUseCases | None = None

    @property
    def logging(self) -> Logger:
        return self._logging

    @property
    def application_configuration(self) -> ApplicationConfiguration:
        return self._configuration

    @property
    def server(self) -> AsgiServer:
        return self._server

    @property
    def use_cases(self) -> ShopUseCases:
        if self._use_cases_after_boot is None:
            raise RuntimeError("The shop container is not booted")
        return self._use_cases_after_boot

    @cached_property
    def actuator(self) -> Actuator:
        return Actuator(
            name=APPLICATION_NAME,
            version=APPLICATION_VERSION,
            environment=APPLICATION_DEPLOYMENT_ENVIRONMENT,
            authors=APPLICATION_AUTHORS_EMAIL,
            is_ready=lambda: self.is_ready,
        )

    async def boot(self) -> None:
        repository = await self._shop_database.connect()
        await reset_schema(repository)
        await self._seed.plant(repository)
        self._use_cases_after_boot = self._use_cases(repository)
        self._ready = True
        self.logging.info(f"Shop booted with {self._seed.products} products")

    async def stop(self) -> None:
        self._ready = False
        await self._stop_repositories()
        self.logging.info("Shop shut down")

    @property
    def is_ready(self) -> bool:
        return self._ready
