class ProductNotFound(Exception):
    def __init__(self, sku: str) -> None:
        super().__init__(f"No product {sku!r}")
        self.sku = sku
