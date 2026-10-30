from decimal import Decimal

import pytest

from shop.domain.exception.product_not_found import ProductNotFound
from shop.domain.order.order import Order
from shop.domain.order.order_line import OrderLine
from shop.domain.order.order_request import OrderRequest
from tests.shop.fakes import KETTLE, MUG, QUOTE

REQUEST = OrderRequest("acme", (OrderLine("SKU-00001", 2), OrderLine("SKU-00002", 3)))


def test_an_order_is_priced_with_discount_then_tax() -> None:
    order = Order.price(REQUEST, {KETTLE.sku: KETTLE, MUG.sku: MUG}, QUOTE)

    assert [line.line_total for line in order.lines] == [Decimal("99.80"), Decimal("29.97")]
    assert order.subtotal == Decimal("129.77")
    assert order.discount == Decimal("6.49")
    assert order.tax == Decimal("24.66")
    assert order.total == Decimal("147.94")
    assert order.items == 5


def test_the_reference_depends_only_on_the_content_of_the_request() -> None:
    same = OrderRequest("acme", (OrderLine("SKU-00001", 2), OrderLine("SKU-00002", 3)))
    other = OrderRequest("acme", (OrderLine("SKU-00001", 3),))

    assert REQUEST.reference == same.reference
    assert REQUEST.reference != other.reference
    assert REQUEST.reference.startswith("ORD-")


def test_an_unknown_product_cannot_be_priced() -> None:
    with pytest.raises(ProductNotFound, match="SKU-00002"):
        Order.price(REQUEST, {KETTLE.sku: KETTLE}, QUOTE)
