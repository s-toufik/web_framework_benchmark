from shop.application.port.inbound.get_product_port import GetProductPort
from shop.domain.product.label import Label


class RenderLabel:
    def __init__(self, get_product: GetProductPort) -> None:
        self._get_product = get_product

    async def handle(self, sku: str) -> Label:
        return Label.of(await self._get_product.handle(sku))
