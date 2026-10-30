from decimal import Decimal

from shop.domain.product.label import Label
from shop.domain.product.product_offer import ProductOffer
from shop.domain.product.stock import Stock
from tests.shop.fakes import KETTLE, QUOTE


def test_an_offer_adds_the_tax_to_the_price() -> None:
    offer = ProductOffer.of(KETTLE, Stock(KETTLE.sku, 3, "Lyon"), QUOTE)

    assert offer.price_with_tax == Decimal("59.88")
    assert offer.in_stock is True


def test_a_label_shows_the_product_its_price_and_its_stock() -> None:
    label = Label.of(ProductOffer.of(KETTLE, Stock(KETTLE.sku, 0, "Lille"), QUOTE))

    assert "SMART KETTLE" in label.text
    assert "Price      59.88 EUR (tax included)" in label.text
    assert "Stock      0 in Lille" in label.text
    assert "OUT OF STOCK" in label.text
    assert label.text.endswith("\n")
