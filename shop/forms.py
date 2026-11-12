from django import forms

from .cart import MAX_QUANTITY
from .models import Purchase


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=MAX_QUANTITY)


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["person", "address"]
