from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


def convert_purchases(apps, schema_editor):
    Purchase = apps.get_model("shop", "Purchase")
    PurchaseItem = apps.get_model("shop", "PurchaseItem")
    db = schema_editor.connection.alias
    for purchase in Purchase.objects.using(db).select_related("product").iterator():
        product = purchase.product
        PurchaseItem.objects.using(db).create(
            purchase_id=purchase.pk, product_id=product.pk,
            product_name=product.name, unit_price=product.price, quantity=1,
        )
        Purchase.objects.using(db).filter(pk=purchase.pk).update(
            subtotal=product.price, total=product.price,
        )


class Migration(migrations.Migration):
    dependencies = [("shop", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="product", name="kind",
            field=models.CharField(
                max_length=12, default="other",
                choices=[
                    ("t-shirt", "Футболки"), ("shirt", "Рубашки"),
                    ("sweater", "Свитеры"), ("trousers", "Брюки"),
                    ("other", "Другое"),
                ],
            ),
        ),
        *[
            migrations.AddField(
                model_name="purchase", name=name,
                field=models.DecimalField(
                    max_digits=14, decimal_places=2, default=Decimal("0.00"),
                ),
                preserve_default=False,
            )
            for name in ("subtotal", "discount", "total")
        ],
        migrations.CreateModel(
            name="PurchaseItem",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                )),
                ("product_name", models.CharField(max_length=200)),
                ("unit_price", models.PositiveIntegerField()),
                ("quantity", models.PositiveIntegerField()),
                ("product", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to="shop.product",
                )),
                ("purchase", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="items",
                    to="shop.purchase",
                )),
            ],
        ),
        migrations.AddField(
            model_name="purchase", name="checkout_key",
            field=models.UUIDField(editable=False, null=True, unique=True),
        ),
        migrations.RunPython(convert_purchases),
        migrations.RemoveField(model_name="purchase", name="product"),
        migrations.AlterField(
            model_name="purchase", name="person",
            field=models.CharField(max_length=200, verbose_name="Имя"),
        ),
        migrations.AlterField(
            model_name="purchase", name="address",
            field=models.CharField(max_length=200, verbose_name="Адрес доставки"),
        ),
    ]
