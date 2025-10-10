"""
Forms for budget category and item management.
"""

import contextlib
import csv
import io
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BudgetCategory, BudgetItem


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating and editing budget categories."""

    class Meta:
        model = BudgetCategory
        fields = ["name", "color_code", "order"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Lodging, Food, Activities, Transportation",
                    "required": True,
                }
            ),
            "color_code": forms.Select(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0, "value": 0}),
        }
        labels = {"name": _("Category Name"), "color_code": _("Color"), "order": _("Display Order")}
        help_texts = {
            "name": _("Choose a descriptive name for this category."),
            "color_code": _("Select a color to help organize your budget."),
            "order": _("Lower numbers appear first (0 = first)."),
        }

    def __init__(self, *args, trip=None, **kwargs):
        """Initialize form with trip."""
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean_name(self):
        """Validate category name is unique for this trip."""
        name = self.cleaned_data.get("name")
        if not name or len(name.strip()) < 2:
            raise ValidationError(_("Category name must be at least 2 characters long."))

        # Check uniqueness within the trip (excluding current instance if editing)
        if self.trip:
            qs = BudgetCategory.objects.filter(trip=self.trip, name=name.strip())
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_("A category with this name already exists for this trip."))

        return name.strip()

    def save(self, commit=True):
        """Save the category with trip."""
        category = super().save(commit=False)
        if self.trip:
            category.trip = self.trip
        if commit:
            category.save()
        return category


class BudgetItemForm(forms.ModelForm):
    """Form for creating and editing budget items."""

    class Meta:
        model = BudgetItem
        fields = [
            "category",
            "description",
            "estimated_amount",
            "actual_amount",
            "paid_by",
            "payment_date",
            "notes",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Brief description of the expense",
                    "required": True,
                }
            ),
            "estimated_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
            "actual_amount": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0"}
            ),
            "paid_by": forms.Select(attrs={"class": "form-control"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Additional notes about this expense...",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "category": _("Category"),
            "description": _("Description"),
            "estimated_amount": _("Estimated Amount"),
            "actual_amount": _("Actual Amount"),
            "paid_by": _("Paid By"),
            "payment_date": _("Payment Date"),
            "notes": _("Notes"),
        }
        help_texts = {
            "category": _("Optionally categorize this expense."),
            "description": _("Brief description of what this expense is for."),
            "estimated_amount": _("Expected cost in USD."),
            "actual_amount": _("Actual cost paid (leave blank until paid)."),
            "paid_by": _("Who paid for this expense."),
            "payment_date": _("Date when payment was made."),
            "notes": _("Any additional details about this expense."),
        }

    def __init__(self, *args, trip=None, created_by=None, family_members=None, **kwargs):
        """Initialize form with trip, creator, and family members."""
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.created_by = created_by

        # Limit category choices to categories for this trip
        if trip:
            self.fields["category"].queryset = BudgetCategory.objects.filter(trip=trip)
            self.fields["category"].empty_label = "-- No Category --"

        # Limit paid_by choices to family members
        if family_members:
            self.fields["paid_by"].queryset = family_members
            self.fields["paid_by"].empty_label = "-- Not Paid Yet --"

    def clean_description(self):
        """Validate description."""
        description = self.cleaned_data.get("description")
        if not description or len(description.strip()) < 2:
            raise ValidationError(_("Description must be at least 2 characters long."))
        return description.strip()

    def clean_estimated_amount(self):
        """Validate estimated amount."""
        amount = self.cleaned_data.get("estimated_amount")
        if amount is not None and amount < 0:
            raise ValidationError(_("Estimated amount cannot be negative."))
        return amount

    def clean_actual_amount(self):
        """Validate actual amount."""
        amount = self.cleaned_data.get("actual_amount")
        if amount is not None and amount < 0:
            raise ValidationError(_("Actual amount cannot be negative."))
        return amount

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        actual_amount = cleaned_data.get("actual_amount")
        paid_by = cleaned_data.get("paid_by")
        payment_date = cleaned_data.get("payment_date")

        # If actual amount is set, payment info should be provided
        if actual_amount is not None:
            if not paid_by:
                self.add_error("paid_by", _("Please specify who paid for this expense."))
            if not payment_date:
                self.add_error("payment_date", _("Please specify when this was paid."))

        return cleaned_data

    def save(self, commit=True):
        """Save the budget item with trip and creator."""
        item = super().save(commit=False)
        if self.trip:
            item.trip = self.trip
        if self.created_by and not item.created_by:
            item.created_by = self.created_by
        if commit:
            item.save()
        return item


class BudgetCSVImportForm(forms.Form):
    """Form for importing budget items from CSV."""

    csv_file = forms.FileField(
        label=_("CSV File"),
        help_text=_(
            "Upload a CSV file with columns: description, estimated_amount, category, actual_amount, paid_by, payment_date, notes"
        ),
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )

    def __init__(self, *args, trip=None, family_members=None, **kwargs):
        """Initialize form with trip and family members."""
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.family_members = family_members

    def clean_csv_file(self):
        """Validate CSV file format."""
        csv_file = self.cleaned_data.get("csv_file")

        if not csv_file:
            raise ValidationError(_("Please upload a CSV file."))

        if not csv_file.name.endswith(".csv"):
            raise ValidationError(_("File must be a CSV file."))

        # Check file size (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise ValidationError(_("File size must be less than 5MB."))

        return csv_file

    def parse_csv(self):
        """Parse CSV file and return list of budget item data."""
        csv_file = self.cleaned_data["csv_file"]

        # Read file content
        file_content = csv_file.read().decode("utf-8")
        csv_file.seek(0)  # Reset file pointer

        reader = csv.DictReader(io.StringIO(file_content))

        items_data = []
        errors = []

        # Expected columns
        required_columns = ["description", "estimated_amount"]
        optional_columns = ["category", "actual_amount", "paid_by", "payment_date", "notes"]

        # Check if required columns exist
        if not all(col in reader.fieldnames for col in required_columns):
            raise ValidationError(
                _("CSV must contain at least these columns: {}").format(", ".join(required_columns))
            )

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Required fields
                description = row.get("description", "").strip()
                if not description:
                    errors.append(f"Row {row_num}: Description is required")
                    continue

                # Parse estimated amount
                try:
                    estimated_amount = Decimal(row.get("estimated_amount", "0").strip())
                    if estimated_amount < 0:
                        errors.append(f"Row {row_num}: Estimated amount cannot be negative")
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_num}: Invalid estimated amount")
                    continue

                # Optional fields
                category_name = row.get("category", "").strip()
                category = None
                if category_name and self.trip:
                    with contextlib.suppress(BudgetCategory.DoesNotExist):
                        category = BudgetCategory.objects.get(trip=self.trip, name=category_name)

                # Parse actual amount
                actual_amount = None
                actual_amount_str = row.get("actual_amount", "").strip()
                if actual_amount_str:
                    try:
                        actual_amount = Decimal(actual_amount_str)
                        if actual_amount < 0:
                            errors.append(f"Row {row_num}: Actual amount cannot be negative")
                            actual_amount = None
                    except (InvalidOperation, ValueError):
                        errors.append(f"Row {row_num}: Invalid actual amount, skipping")

                # Parse paid_by
                paid_by = None
                paid_by_str = row.get("paid_by", "").strip()
                if paid_by_str and self.family_members:
                    # Try to match by username, email, or full name
                    for member in self.family_members:
                        if paid_by_str.lower() in [
                            member.username.lower(),
                            member.email.lower(),
                            member.get_full_name().lower(),
                        ]:
                            paid_by = member
                            break

                # Parse payment_date
                payment_date = None
                payment_date_str = row.get("payment_date", "").strip()
                if payment_date_str:
                    from datetime import datetime

                    # Try different date formats
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y"]:
                        try:
                            payment_date = datetime.strptime(payment_date_str, fmt).date()
                            break
                        except ValueError:
                            continue

                    if not payment_date:
                        errors.append(
                            f"Row {row_num}: Invalid payment date format (use YYYY-MM-DD)"
                        )

                # Notes
                notes = row.get("notes", "").strip()

                items_data.append(
                    {
                        "description": description,
                        "estimated_amount": estimated_amount,
                        "category": category,
                        "actual_amount": actual_amount,
                        "paid_by": paid_by,
                        "payment_date": payment_date,
                        "notes": notes,
                    }
                )

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        if errors:
            raise ValidationError(
                _("CSV import errors:\n{}").format("\n".join(errors[:10]))
            )  # Show first 10 errors

        if not items_data:
            raise ValidationError(_("No valid data found in CSV file."))

        return items_data
