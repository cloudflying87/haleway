from django import forms

from .models import (
    GroceryListTemplate,
    TripGroceryItem,
    TripGroceryList,
)


class GroceryListTemplateForm(forms.ModelForm):
    """Form for creating/editing grocery list templates"""

    class Meta:
        model = GroceryListTemplate
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Summer Beach Trip Groceries"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description of this template",
                }
            ),
        }


class TripGroceryListForm(forms.ModelForm):
    """Form for creating/editing trip grocery lists"""

    class Meta:
        model = TripGroceryList
        fields = ["name", "assigned_to", "shopping_date", "store_name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Week 1 Groceries"}
            ),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "shopping_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "store_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Walmart, Costco, Local Market",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        trip = kwargs.pop("trip", None)
        super().__init__(*args, **kwargs)

        # Make all optional fields not required
        self.fields["assigned_to"].required = False
        self.fields["shopping_date"].required = False
        self.fields["store_name"].required = False

        # Populate assigned_to with family members from the trip
        if trip:
            from apps.accounts.models import User

            family_member_user_ids = trip.family.members.values_list("user_id", flat=True)
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=family_member_user_ids)
            self.fields["assigned_to"].empty_label = "Not assigned"


class TripGroceryItemForm(forms.ModelForm):
    """Form for adding/editing individual grocery items"""

    class Meta:
        model = TripGroceryItem
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
                attrs={"class": "form-control", "placeholder": "e.g., Bananas, Milk, Chips"}
            ),
            "quantity": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., 2 lbs, 1 gallon, 6 pack"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Optional notes"}
            ),
        }

    def __init__(self, *args, **kwargs):
        grocery_list = kwargs.pop("grocery_list", None)
        super().__init__(*args, **kwargs)
        self.fields["quantity"].required = False
        self.fields["notes"].required = False

        # Store category suggestions in form for template rendering
        if grocery_list:
            # Get distinct categories from this grocery list
            existing_categories = list(
                TripGroceryItem.objects.filter(grocery_list=grocery_list)
                .values_list("category", flat=True)
                .distinct()
                .order_by("category")
            )

            # Add common category suggestions
            common_categories = [
                "Produce",
                "Dairy",
                "Meat",
                "Snacks",
                "Beverages",
                "Breakfast",
                "Lunch/Dinner",
                "Household",
                "Health",
                "Frozen",
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


class BulkGroceryItemForm(forms.Form):
    """Form for bulk adding grocery items"""

    CATEGORY_CHOICES = [
        ("Groceries", "Groceries"),
        ("Produce", "Produce"),
        ("Dairy", "Dairy"),
        ("Meat", "Meat"),
        ("Snacks", "Snacks"),
        ("Beverages", "Beverages"),
        ("Breakfast", "Breakfast"),
        ("Lunch/Dinner", "Lunch/Dinner"),
        ("Household", "Household"),
        ("Health", "Health"),
        ("Other", "Other"),
    ]

    items_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": "Enter items separated by commas or new lines.\n\nExamples:\nBananas, Milk, Chips, Water\n\nOr with quantities:\nBananas | 2 lbs, Milk | 1 gallon, Chips\n\nOr one per line:\nBananas\nMilk\nChips",
            }
        ),
        help_text="Separate items with commas or new lines. Use | to add quantity (optional).",
        label="Items",
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        initial="Groceries",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Optional: Organize items into a category",
    )

    def clean_items_text(self):
        """Parse the items text and validate"""
        items_text = self.cleaned_data.get("items_text", "")

        # Split by both newlines AND commas
        # First split by newlines, then split each line by commas
        raw_items = []
        for line in items_text.split("\n"):
            # Split each line by comma
            items_on_line = [item.strip() for item in line.split(",") if item.strip()]
            raw_items.extend(items_on_line)

        if not raw_items:
            raise forms.ValidationError("Please enter at least one item.")

        # Store parsed items for later use
        self.parsed_items = []
        for item_text in raw_items:
            if "|" in item_text:
                parts = item_text.split("|", 1)
                item_name = parts[0].strip()
                quantity = parts[1].strip() if len(parts) > 1 else ""
            else:
                item_name = item_text.strip()
                quantity = ""

            if item_name:
                self.parsed_items.append({"item_name": item_name, "quantity": quantity})

        return items_text


class SaveAsTemplateForm(forms.Form):
    """Form for saving a grocery list as a template"""

    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g., My Custom Beach Trip Groceries"}
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3, "placeholder": "Optional description"}
        ),
    )
