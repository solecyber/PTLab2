from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from shop.cart import CartLine, CartTotals, calculate_totals
from shop.models import Product


class DiscountTests(SimpleTestCase):
    def setUp(self):
        self.tee = Product(name="Футболка", kind=Product.Kind.T_SHIRT, price=1490)
        self.other_tee = Product(name="Футболка плотная", kind=Product.Kind.T_SHIRT, price=1890)
        self.shirt = Product(name="Рубашка", kind=Product.Kind.SHIRT, price=3490)

    def test_empty_cart(self):
        self.assertEqual(calculate_totals([]), CartTotals(0, 0, 0))

    def test_multiple_units_of_one_product_do_not_trigger_discount(self):
        totals = calculate_totals([CartLine(self.tee, 2)])
        self.assertEqual(totals, CartTotals(2980, 0, 2980))

    def test_two_products_of_same_kind_do_not_trigger_discount(self):
        totals = calculate_totals([CartLine(self.tee, 1), CartLine(self.other_tee, 1)])
        self.assertEqual(totals, CartTotals(3380, 0, 3380))

    def test_discount_applies_to_every_unit_in_mixed_cart(self):
        totals = calculate_totals([CartLine(self.tee, 2), CartLine(self.shirt, 1)])
        self.assertEqual(totals, CartTotals(6470, 647, 5823))

    def test_fractional_rubles_are_preserved(self):
        self.tee.price = 101
        self.shirt.price = 222
        totals = calculate_totals([CartLine(self.tee, 1), CartLine(self.shirt, 1)])
        self.assertEqual(totals.discount, Decimal("32.30"))
        self.assertEqual(totals.total, Decimal("290.70"))


class CatalogTests(TestCase):
    def test_data_migration_populates_catalog(self):
        self.assertTrue(Product.objects.filter(name="Льняная рубашка").exists())
        self.assertGreaterEqual(Product.objects.values("kind").distinct().count(), 2)
