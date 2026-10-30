from typing import Annotated

from pydantic import BaseModel, Field

from shop.domain.order.order import Order
from shop.domain.order.order_line import OrderLine
from shop.domain.order.order_request import OrderRequest


class OrderLineSchema(BaseModel):
    sku: Annotated[str, Field(pattern=r"^SKU-\d{5}$")]
    quantity: Annotated[int, Field(ge=1, le=100)]


class OrderRequestSchema(BaseModel):
    customer: Annotated[str, Field(min_length=1, max_length=64)]
    lines: Annotated[list[OrderLineSchema], Field(min_length=1, max_length=20)]

    def to_domain(self) -> OrderRequest:
        return OrderRequest(
            customer=self.customer,
            lines=tuple(OrderLine(line.sku, line.quantity) for line in self.lines),
        )


class PricedLineSchema(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: str
    line_total: str


class OrderSchema(BaseModel):
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
