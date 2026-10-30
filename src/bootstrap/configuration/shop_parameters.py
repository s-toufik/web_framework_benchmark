from dataclasses import dataclass

from pycraftcore.application_configuration.model.server import AsgiServer


@dataclass(frozen=True, slots=True)
class ShopParameters:
    seed: int
    products: int
    image_bytes: int

    @classmethod
    def of(cls, server: AsgiServer) -> ShopParameters:
        return cls(
            seed=int(server.parameters["seed"]),
            products=int(server.parameters["products"]),
            image_bytes=int(server.parameters["image_bytes"]),
        )
