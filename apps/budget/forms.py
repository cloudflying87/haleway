"""
Forms for budget category and item management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import BudgetCategory, BudgetItem


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating and editing budget categories."""

    class Meta:
        model = BudgetCategory
        fields = ['name', 'color_code', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Lodging, Food, Activities, Transportation',
                'required': True
            }),
            'color_code': forms.Select(attrs={
                'class': 'form-control'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            })
        }
        labels = {
            'name': _('Category Name'),
            'color_code': _('Color'),
            'order': _('Display Order')
        }
        help_texts = {
            'name': _('Choose a descriptive name for this category.'),
            'color_code': _('Select a color to help organize your budget.'),
            'order': _('Lower numbers appear first (0 = first).')
        }

    def __init__(self, *args, trip=None, **kwargs):
        """Initialize form with trip."""
        super().__init__(*args, **kwargs)
        self.trip = trip

    def clean_name(self):
        """Validate category name is unique for this trip."""
        name = self.cleaned_data.get('name')
        if not name or len(name.strip()) < 2:
            raise ValidationError(_('Category name must be at least 2 characters long.'))

        # Check uniqueness within the trip (excluding current instance if editing)
        if self.trip:
            qs = BudgetCategory.objects.filter(trip=self.trip, name=name.strip())
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(_('A category with this name already exists for this trip.'))

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
        fields = ['category', 'description', 'estimated_amount', 'actual_amount',
                  'paid_by', 'payment_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the expense',
                'required': True
            }),
            'estimated_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'actual_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'paid_by': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes about this expense...',
                'rows': 3
            })
        }
        labels = {
            'category': _('Category'),
            'description': _('Description'),
            'estimated_amount': _('Estimated Amount'),
            'actual_amount': _('Actual Amount'),
            'paid_by': _('Paid By'),
            'payment_date': _('Payment Date'),
            'notes': _('Notes')
        }
        help_texts = {
            'category': _('Optionally categorize this expense.'),
            'description': _('Brief description of what this expense is for.'),
            'estimated_amount': _('Expected cost in USD.'),
            'actual_amount': _('Actual cost paid (leave blank until paid).'),
            'paid_by': _('Who paid for this expense.'),
            'payment_date': _('Date when payment was made.'),
            'notes': _('Any additional details about this expense.')
        }

    def __init__(self, *args, trip=None, created_by=None, family_members=None, **kwargs):
        """Initialize form with trip, creator, and family members."""
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.created_by = created_by

        # Limit category choices to categories for this trip
        if trip:
            self.fields['category'].queryset = BudgetCategory.objects.filter(trip=trip)
            self.fields['category'].empty_label = '-- No Category --'

        # Limit paid_by choices to family members
        if family_members:
            self.fields['paid_by'].queryset = family_members
            self.fields['paid_by'].empty_label = '-- Not Paid Yet --'

    def clean_description(self):
        """Validate description."""
        description = self.cleaned_data.get('description')
        if not description or len(description.strip()) < 2:
            raise ValidationError(_('Description must be at least 2 characters long.'))
        return description.strip()

    def clean_estimated_amount(self):
        """Validate estimated amount."""
        amount = self.cleaned_data.get('estimated_amount')
        if amount is not None and amount < 0:
            raise ValidationError(_('Estimated amount cannot be negative.'))
        return amount

    def clean_actual_amount(self):
        """Validate actual amount."""
        amount = self.cleaned_data.get('actual_amount')
        if amount is not None and amount < 0:
            raise ValidationError(_('Actual amount cannot be negative.'))
        return amount

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        actual_amount = cleaned_data.get('actual_amount')
        paid_by = cleaned_data.get('paid_by')
        payment_date = cleaned_data.get('payment_date')

        # If actual amount is set, payment info should be provided
        if actual_amount is not None:
            if not paid_by:
                self.add_error('paid_by', _('Please specify who paid for this expense.'))
            if not payment_date:
                self.add_error('payment_date', _('Please specify when this was paid.'))

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
