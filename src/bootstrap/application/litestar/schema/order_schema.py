from typing import Annotated

import msgspec

from shop.domain.order.order import Order
from shop.domain.order.order_line import OrderLine
from shop.domain.order.order_request import OrderRequest


class OrderLineSchema(msgspec.Struct):
    sku: Annotated[str, msgspec.Meta(pattern=r"^SKU-\d{5}$")]
    quantity: Annotated[int, msgspec.Meta(ge=1, le=100)]


class OrderRequestSchema(msgspec.Struct):
    customer: Annotated[str, msgspec.Meta(min_length=1, max_length=64)]
    lines: Annotated[list[OrderLineSchema], msgspec.Meta(min_length=1, max_length=20)]

    def to_domain(self) -> OrderRequest:
        return OrderRequest(
            customer=self.customer,
            lines=tuple(OrderLine(line.sku, line.quantity) for line in self.lines),
        )


class PricedLineSchema(msgspec.Struct):
    sku: str
    name: str
    quantity: int
    unit_price: str
    line_total: str


class OrderSchema(msgspec.Struct):
    reference: str
    customer: str
    lines: list[PricedLineSchema]
    subtotal: str
    discount: str
    tax: str
    total: str

    @classmethod
    def of(cls, order: Order) -> OrderSchema:
        return cls(
            reference=order.reference,
            customer=order.customer,
            lines=[
                PricedLineSchema(
                    sku=line.sku,
                    name=line.name,
                    quantity=line.quantity,
                    unit_price=str(line.unit_price),
                    line_total=str(line.line_total),
                )
                for line in order.lines
            ],
            subtotal=str(order.subtotal),
            discount=str(order.discount),
            tax=str(order.tax),
            total=str(order.total),
        )
