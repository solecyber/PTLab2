from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("buy/<int:product_id>/", views.add_product, name="buy"),
    path("cart/", views.cart, name="cart"),
    path("cart/<int:product_id>/", views.update_product, name="update_product"),
    path("checkout/", views.checkout, name="checkout"),
    path("receipt/", views.receipt, name="receipt"),
    path("healthz/", views.health, name="health"),
]
