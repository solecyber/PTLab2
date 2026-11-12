from decimal import Decimal
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from shop.cart import CART_KEY, CHECKOUT_KEY
from shop.models import Product, Purchase, PurchaseItem


class ShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tee = Product.objects.create(name="Тестовая футболка", kind=Product.Kind.T_SHIRT, price=1500)
        cls.shirt = Product.objects.create(name="Тестовая рубашка", kind=Product.Kind.SHIRT, price=3500)

    def add(self, product):
        return self.client.post(reverse("buy", args=[product.pk]))

    def update(self, product, quantity):
        return self.client.post(reverse("update_product", args=[product.pk]), {"quantity": quantity})

    def test_catalog_and_empty_cart(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, self.tee.name)
        self.assertContains(self.client.get(reverse("cart")), "Корзина пока пуста.")

    def test_adding_twice_increases_quantity_without_discount(self):
        self.assertRedirects(self.add(self.tee), reverse("cart"))
        self.add(self.tee)
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.context["lines"][0].quantity, 2)
        self.assertEqual(response.context["totals"].discount, 0)

    def test_add_is_limited_to_99_units(self):
        self.update(self.tee, 99)
        self.add(self.tee)
        self.assertEqual(self.client.session[CART_KEY][str(self.tee.pk)], 99)

    def test_update_and_remove_recalculate_discount(self):
        self.add(self.tee)
        self.add(self.shirt)
        self.assertRedirects(self.update(self.tee, 2), reverse("cart"))
        self.assertEqual(self.client.get(reverse("cart")).context["totals"].discount, 650)
        self.assertRedirects(self.update(self.shirt, 0), reverse("cart"))
        self.assertEqual(self.client.get(reverse("cart")).context["totals"].discount, 0)

    def test_bad_quantity_is_rejected(self):
        self.add(self.tee)
        for quantity in (-1, 100, "abc"):
            with self.subTest(quantity=quantity):
                self.assertEqual(self.update(self.tee, quantity).status_code, 400)
        self.assertEqual(self.client.session[CART_KEY][str(self.tee.pk)], 1)

    def test_missing_product_returns_not_found(self):
        self.assertEqual(self.client.post(reverse("buy", args=[9999])).status_code, 404)

    def test_get_cannot_change_cart(self):
        for url in (
            reverse("buy", args=[self.tee.pk]),
            reverse("update_product", args=[self.tee.pk]),
            reverse("checkout"),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("buy", args=[self.tee.pk])).status_code, 403)

    def test_checkout_requires_nonempty_cart(self):
        response = self.client.post(reverse("checkout"), {"person": "Тест", "address": "Дом 1"})
        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Purchase.objects.exists())

    def test_checkout_requires_valid_form(self):
        self.add(self.tee)
        response = self.client.post(reverse("checkout"), {"person": "Тест"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("address", response.context["form"].errors)
        self.assertFalse(Purchase.objects.exists())

    def test_checkout_persists_totals_and_snapshot_and_clears_cart(self):
        self.add(self.tee)
        self.add(self.shirt)
        response = self.client.post(reverse("checkout"), {
            "person": "Тест", "address": "Учебная улица, 1", "total": "0",
        })
        self.assertRedirects(response, reverse("receipt"))
        purchase = Purchase.objects.get()
        self.assertEqual(purchase.subtotal, Decimal("5000.00"))
        self.assertEqual(purchase.discount, Decimal("500.00"))
        self.assertEqual(purchase.total, Decimal("4500.00"))
        self.assertEqual(purchase.items.count(), 2)
        self.tee.delete()
        item = PurchaseItem.objects.get(purchase=purchase, product__isnull=True)
        self.assertEqual(item.product_name, "Тестовая футболка")
        self.assertEqual(item.unit_price, 1500)
        self.assertEqual(item.quantity, 1)
        self.assertNotIn(CART_KEY, self.client.session)
        self.assertContains(self.client.get(reverse("receipt")), "Заказ оформлен")
        self.assertEqual(Client().get(reverse("receipt")).status_code, 404)

    def test_retry_with_same_cart_does_not_duplicate_order(self):
        self.add(self.tee)
        pending = dict(self.client.session)
        data = {"person": "Тест", "address": "Дом 1"}
        self.client.post(reverse("checkout"), data)
        session = self.client.session
        session.update({CART_KEY: pending[CART_KEY], CHECKOUT_KEY: pending[CHECKOUT_KEY]})
        session.save()
        self.assertRedirects(self.client.post(reverse("checkout"), data), reverse("receipt"))
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(PurchaseItem.objects.count(), 1)

    def test_failed_line_save_does_not_leave_partial_order(self):
        self.add(self.tee)
        with patch("shop.views.PurchaseItem.objects.bulk_create", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("checkout"), {"person": "Тест", "address": "Дом 1"})
        self.assertFalse(Purchase.objects.exists())
        self.assertIn(CART_KEY, self.client.session)

    def test_health_check(self):
        self.assertContains(self.client.get(reverse("health")), "ok")
