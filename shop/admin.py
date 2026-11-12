from django.contrib import admin

from .models import Product, Purchase, PurchaseItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "price")
    list_filter = ("kind",)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "subtotal", "discount", "total")
    inlines = (PurchaseItemInline,)
