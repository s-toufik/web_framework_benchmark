from functools import cached_property

from pycraftcore.application_configuration import ApplicationConfiguration
from pycraftcore.application_configuration.model.server import AsgiServer
from pycraftcore.logger import configure_logging
from pycraftcore.logger.adapter import StandardLogger
from pycraftcore.logger.port import Logger
from pycraftcore.repository.port import AsyncRepositoryFactory

from bootstrap.configuration.application_configuration import SetApplicationConfiguration
from bootstrap.configuration.application_logger import create_logger
from bootstrap.configuration.settings import ProcessSettings


class BaseDI:
    def __init__(self, settings: ProcessSettings) -> None:
        self._settings = settings
        self._repositories: list[AsyncRepositoryFactory] = []

    @cached_property
    def _configuration(self) -> ApplicationConfiguration:
        configuration = SetApplicationConfiguration(self._settings)()
        configure_logging(configuration.log)
        return configuration

    @cached_property
    def _logging(self) -> Logger:
        return create_logger(StandardLogger())

    @cached_property
    def _server(self) -> AsgiServer:
        return self._configuration.server.asgi(self._settings.role)

    def _register_repository(self, repository: AsyncRepositoryFactory) -> AsyncRepositoryFactory:
        self._repositories.append(repository)
        return repository

    async def _stop_repositories(self) -> None:
        for repository in self._repositories:
            await repository.disconnect()
