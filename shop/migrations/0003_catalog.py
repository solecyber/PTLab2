from django.db import migrations


def seed_catalog(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    products = [
        ("Футболка из хлопка", "t-shirt", 1490),
        ("Футболка плотная", "t-shirt", 1890),
        ("Льняная рубашка", "shirt", 3490),
        ("Рубашка свободного кроя", "shirt", 2990),
        ("Свитер фактурной вязки", "sweater", 3990),
        ("Брюки прямого кроя", "trousers", 4290),
    ]
    for name, kind, price in products:
        Product.objects.using(schema_editor.connection.alias).get_or_create(
            name=name, defaults={"kind": kind, "price": price},
        )


class Migration(migrations.Migration):
    dependencies = [("shop", "0002_clothing_orders")]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
