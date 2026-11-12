from uuid import uuid4

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_safe

from .cart import CART_KEY, CHECKOUT_KEY, MAX_QUANTITY, calculate_totals, get_cart
from .forms import CheckoutForm, QuantityForm
from .models import Product, Purchase, PurchaseItem


def render_cart(request, form=None, status=200):
    lines = get_cart(request.session)
    return render(request, "shop/cart.html", {
        "lines": lines,
        "totals": calculate_totals(lines),
        "form": form if form is not None else CheckoutForm(),
        "max_quantity": MAX_QUANTITY,
    }, status=status)


@require_safe
def index(request):
    products = Product.objects.order_by("pk")
    return render(request, "shop/index.html", {
        "products": products,
        "cart_count": sum(line.quantity for line in get_cart(request.session)),
    })


@require_POST
def add_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantities = request.session.get(CART_KEY, {})
    key = str(product.pk)
    quantities[key] = min(quantities.get(key, 0) + 1, MAX_QUANTITY)
    request.session[CART_KEY] = quantities
    request.session[CHECKOUT_KEY] = uuid4().hex
    return redirect("cart")


@require_POST
def update_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = QuantityForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Укажите количество от 0 до 99.", status=400)

    quantities = request.session.get(CART_KEY, {})
    key = str(product.pk)
    quantity = form.cleaned_data["quantity"]
    if quantity:
        quantities[key] = quantity
    else:
        quantities.pop(key, None)
    request.session[CART_KEY] = quantities
    request.session[CHECKOUT_KEY] = uuid4().hex
    return redirect("cart")


@require_safe
def cart(request):
    return render_cart(request)


@require_POST
def checkout(request):
    lines = get_cart(request.session)
    if not lines:
        return redirect("cart")
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render_cart(request, form, status=400)

    totals = calculate_totals(lines)
    with transaction.atomic():
        purchase, created = Purchase.objects.get_or_create(
            checkout_key=request.session[CHECKOUT_KEY],
            defaults={
                **form.cleaned_data, "subtotal": totals.subtotal,
                "discount": totals.discount, "total": totals.total,
            },
        )
        if created:
            PurchaseItem.objects.bulk_create([
                PurchaseItem(
                    purchase=purchase, product=line.product,
                    product_name=line.product.name, unit_price=line.product.price,
                    quantity=line.quantity,
                )
                for line in lines
            ])
    request.session.pop(CART_KEY, None)
    request.session.pop(CHECKOUT_KEY, None)
    request.session["last_purchase"] = purchase.pk
    return redirect("receipt")


@require_safe
def receipt(request):
    purchase = get_object_or_404(
        Purchase, pk=request.session.get("last_purchase"),
    )
    return render(request, "shop/receipt.html", {"purchase": purchase})


@require_safe
def health(request):
    return HttpResponse("ok", content_type="text/plain")
