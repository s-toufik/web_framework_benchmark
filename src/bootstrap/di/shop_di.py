from functools import cached_property
from typing import Final

from pycraftcore.application_configuration.model.connector import DatabaseConnector
from pycraftcore.repository.adapter import SqliteRepositoryFactory, SqliteSettingsMapper
from pycraftcore.repository.port import AsyncRepository, AsyncRepositoryFactory

from bootstrap.configuration.shop_parameters import ShopParameters
from bootstrap.di.base_di import BaseDI
from shop.adapter.outbound.api.fake_inventory_api import FakeInventoryApi
from shop.adapter.outbound.api.fake_market_feed import FakeMarketFeed
from shop.adapter.outbound.api.fake_pricing_api import FakePricingApi
from shop.adapter.outbound.sqlite.catalog_seed import CatalogSeed
from shop.adapter.outbound.sqlite.sqlite_file_repository import SqliteFileRepository
from shop.adapter.outbound.sqlite.sqlite_note_repository import SqliteNoteRepository
from shop.adapter.outbound.sqlite.sqlite_order_repository import SqliteOrderRepository
from shop.adapter.outbound.sqlite.sqlite_product_repository import SqliteProductRepository
from shop.application.use_case.follow_product import FollowProduct
from shop.application.use_case.get_product import GetProduct
from shop.application.use_case.get_product_image import GetProductImage
from shop.application.use_case.place_order import PlaceOrder
from shop.application.use_case.render_label import RenderLabel
from shop.application.use_case.save_note import SaveNote
from shop.application.use_case.shop_use_cases import ShopUseCases
from shop.application.use_case.store_file import StoreFile
from shop.application.use_case.track_order import TrackOrder

SHOP_DATABASE: Final[str] = "shop_db"
MILLISECONDS: Final[float] = 1_000


class ShopDI(BaseDI):
    @cached_property
    def _parameters(self) -> ShopParameters:
        return ShopParameters.of(self._server)

    @cached_property
    def _seed(self) -> CatalogSeed:
        parameters = self._parameters
        return CatalogSeed(parameters.seed, parameters.products, parameters.image_bytes)

    @cached_property
    def _shop_database(self) -> AsyncRepositoryFactory:
        connector: DatabaseConnector = self._configuration.connector.database(SHOP_DATABASE)
        return self._register_repository(SqliteRepositoryFactory(SqliteSettingsMapper(connector)()))

    @cached_property
    def _inventory(self) -> FakeInventoryApi:
        return FakeInventoryApi(self._milliseconds("inventory_stock", "latency_ms"))

    @cached_property
    def _pricing(self) -> FakePricingApi:
        return FakePricingApi(self._milliseconds("pricing_quote", "latency_ms"))

    @cached_property
    def _market(self) -> FakeMarketFeed:
        parameters = self._configuration.operation.api("market_ticks").parameters
        return FakeMarketFeed(
            self._milliseconds("market_ticks", "interval_ms"), int(parameters["ticks"])
        )

    def _use_cases(self, repository: AsyncRepository) -> ShopUseCases:
        products = SqliteProductRepository(repository)
        orders = SqliteOrderRepository(repository)
        get_product = GetProduct(products, self._inventory, self._pricing)
        return ShopUseCases(
            get_product=get_product,
            place_order=PlaceOrder(products, self._pricing, orders),
            follow_product=FollowProduct(products, self._market),
            track_order=TrackOrder(products, self._pricing, self._inventory, orders),
            get_product_image=GetProductImage(products),
            store_file=StoreFile(SqliteFileRepository(repository)),
            render_label=RenderLabel(get_product),
            save_note=SaveNote(SqliteNoteRepository(repository)),
        )

    def _milliseconds(self, operation: str, parameter: str) -> float:
        parameters = self._configuration.operation.api(operation).parameters
        return float(parameters[parameter]) / MILLISECONDS
