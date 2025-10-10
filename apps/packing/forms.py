"""
Forms for packing list management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import PackingListTemplate, TripPackingItem


class PackingListTemplateForm(forms.ModelForm):
    """Form for creating/editing packing list templates."""

    class Meta:
        model = PackingListTemplate
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "e.g., My Custom Beach List"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 3,
                    "placeholder": "Optional description of this template",
                }
            ),
        }


class PackingItemForm(forms.ModelForm):
    """Form for adding/editing packing items."""

    class Meta:
        model = TripPackingItem
        fields = ["category", "item_name", "quantity", "notes"]
        widgets = {
            "category": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Select or type category",
                    "list": "category-datalist",
                }
            ),
            "item_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Sunscreen, Hiking boots"}
            ),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1, "value": 1}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Optional notes about this item",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with category suggestions from packing list."""
        packing_list = kwargs.pop("packing_list", None)
        super().__init__(*args, **kwargs)

        # Store category suggestions in form for template rendering
        if packing_list:
            # Get distinct categories from this packing list
            existing_categories = list(
                TripPackingItem.objects.filter(packing_list=packing_list)
                .values_list("category", flat=True)
                .distinct()
                .order_by("category")
            )

            # Add common category suggestions
            common_categories = [
                "Clothing",
                "Electronics",
                "Toiletries",
                "Documents",
                "Medications",
                "Beach Gear",
                "Outdoor Gear",
                "Sports Equipment",
                "Entertainment",
                "Food & Snacks",
            ]

            # Combine existing + common (deduplicated)
            all_categories = existing_categories.copy()
            for cat in common_categories:
                if cat not in all_categories:
                    all_categories.append(cat)

            # Store for template access
            self.category_suggestions = all_categories
        else:
            self.category_suggestions = []


class OutfitCalculatorForm(forms.Form):
    """Form for calculating outfit items based on number of outfits."""

    category = forms.CharField(
        label=_("Category"),
        max_length=100,
        initial="Clothing",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., Clothing, Norah's Clothes, David's Clothes",
                "list": "category-suggestions",
            }
        ),
        help_text=_("Choose which category these outfit items should be added to"),
    )

    num_outfits = forms.IntegerField(
        label=_("Number of outfits"),
        min_value=1,
        max_value=30,
        initial=5,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g., 5"}),
        help_text=_("We'll calculate shirts, pants, underwear, and socks based on this number."),
    )


class BulkPackingItemForm(forms.Form):
    """Form for adding multiple items at once via comma-separated input."""

    category = forms.CharField(
        label=_("Category"),
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "e.g., Clothing, Electronics, Toiletries",
                "list": "category-suggestions",
            }
        ),
        help_text=_("Create a new category or use an existing one"),
    )

    items = forms.CharField(
        label=_("Items (comma-separated)"),
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-textarea",
                "rows": 6,
                "placeholder": "Sunscreen, Hat-2, Beach towel, Sunglasses-3, Water bottle",
            }
        ),
        help_text=_('Add items separated by commas. Use "item-3" to set quantity to 3.'),
    )

    def clean_items(self):
        """Parse and validate the comma-separated items."""
        items_text = self.cleaned_data["items"]

        if not items_text.strip():
            raise forms.ValidationError(_("Please enter at least one item."))

        # Split by comma and clean up
        raw_items = [item.strip() for item in items_text.split(",")]
        raw_items = [item for item in raw_items if item]  # Remove empty strings

        if not raw_items:
            raise forms.ValidationError(_("Please enter at least one item."))

        # Parse items with quantities
        parsed_items = []
        for item in raw_items:
            # Check if item has quantity syntax (e.g., "Sunscreen-3")
            if "-" in item:
                parts = item.rsplit("-", 1)  # Split from the right to handle items with hyphens
                if len(parts) == 2 and parts[1].isdigit():
                    item_name = parts[0].strip()
                    quantity = int(parts[1])
                    if quantity < 1:
                        raise forms.ValidationError(_(f'Quantity must be at least 1 for "{item}"'))
                    parsed_items.append({"name": item_name, "quantity": quantity})
                    continue

            # No quantity specified, default to 1
            parsed_items.append({"name": item, "quantity": 1})

        return parsed_items
