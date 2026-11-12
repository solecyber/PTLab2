from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .models import Product

MAX_QUANTITY = 99
DISCOUNT_RATE = Decimal("0.10")
CART_KEY = "cart"
CHECKOUT_KEY = "checkout_key"


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int

    @property
    def total(self):
        return self.product.price * self.quantity


@dataclass(frozen=True)
class CartTotals:
    subtotal: Decimal
    discount: Decimal
    total: Decimal


def get_cart(session):
    quantities = session.get(CART_KEY, {})
    products = Product.objects.filter(pk__in=quantities).order_by("pk")
    return [CartLine(product, quantities[str(product.pk)]) for product in products]


def calculate_totals(lines):
    subtotal = Decimal(sum(line.total for line in lines))
    kinds = {line.product.kind for line in lines}
    discount = Decimal("0.00")
    if len(kinds) >= 2:
        discount = (subtotal * DISCOUNT_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
    return CartTotals(subtotal, discount, subtotal - discount)
