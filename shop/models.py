from django.db import models


class Product(models.Model):
    class Kind(models.TextChoices):
        T_SHIRT = "t-shirt", "Футболки"
        SHIRT = "shirt", "Рубашки"
        SWEATER = "sweater", "Свитеры"
        TROUSERS = "trousers", "Брюки"
        OTHER = "other", "Другое"

    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.OTHER)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    person = models.CharField("Имя", max_length=200)
    address = models.CharField("Адрес доставки", max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    checkout_key = models.UUIDField(unique=True, null=True, editable=False)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="items",
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
    )
    product_name = models.CharField(max_length=200)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
