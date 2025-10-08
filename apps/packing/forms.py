"""
Forms for packing list management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    PackingListTemplate,
    PackingListTemplateItem,
    TripPackingList,
    TripPackingItem
)


class PackingListTemplateForm(forms.ModelForm):
    """Form for creating/editing packing list templates."""

    class Meta:
        model = PackingListTemplate
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., My Custom Beach List'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Optional description of this template'
            }),
        }


class TripPackingListForm(forms.ModelForm):
    """Form for creating/editing trip packing lists."""

    class Meta:
        model = TripPackingList
        fields = ['name', 'assigned_to']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': "e.g., David's List, Beach Gear"
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class PackingItemForm(forms.ModelForm):
    """Form for adding/editing packing items."""

    class Meta:
        model = TripPackingItem
        fields = ['category', 'item_name', 'quantity', 'notes']
        widgets = {
            'category': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Clothing, Electronics, Toiletries',
                'list': 'category-suggestions'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Sunscreen, Hiking boots'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'value': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Optional notes about this item'
            }),
        }


class OutfitCalculatorForm(forms.Form):
    """Form for calculating outfit items based on number of outfits."""

    num_outfits = forms.IntegerField(
        label=_('Number of outfits'),
        min_value=1,
        max_value=30,
        initial=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 5'
        }),
        help_text=_('We\'ll calculate shirts, pants, underwear, and socks based on this number.')
    )
