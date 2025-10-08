"""
Forms for trip management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Trip, Resort


class TripForm(forms.ModelForm):
    """Form for creating and editing trips."""

    class Meta:
        model = Trip
        fields = ['name', 'destination_name', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Hawaii 2025',
            }),
            'destination_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Maui, Hawaii',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def clean(self):
        """Validate that end_date is after start_date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('End date must be after start date.')
                })

        return cleaned_data


class ResortForm(forms.ModelForm):
    """Form for resort details."""

    class Meta:
        model = Resort
        fields = [
            'name', 'website_url', 'phone_number',
            'check_in_time', 'check_out_time',
            'address_line1', 'address_line2',
            'city', 'state', 'zip_code', 'country',
            'latitude', 'longitude',
            'general_notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resort or hotel name',
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.resort-website.com',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567',
            }),
            'check_in_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'check_out_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address',
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apt, suite, unit, etc. (optional)',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State or Province',
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zip or Postal Code',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 21.3099',
                'step': 'any',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., -157.8581',
                'step': 'any',
            }),
            'general_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Confirmation numbers, check-in info, parking details, etc.',
            }),
        }


class TripResortForm(forms.Form):
    """Combined form for trip and resort creation."""

    # Trip fields
    trip_name = forms.CharField(
        max_length=200,
        label=_('Trip Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Hawaii 2025',
        })
    )
    destination_name = forms.CharField(
        max_length=200,
        label=_('Destination'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Maui, Hawaii',
        })
    )
    start_date = forms.DateField(
        label=_('Start Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    end_date = forms.DateField(
        label=_('End Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    # Resort fields (optional on creation)
    resort_name = forms.CharField(
        max_length=200,
        required=False,
        label=_('Resort/Hotel Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Resort or hotel name (optional)',
        })
    )
    resort_website = forms.URLField(
        required=False,
        label=_('Website'),
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.resort-website.com (optional)',
        })
    )

    def clean(self):
        """Validate that end_date is after start_date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': _('End date must be after start date.')
                })

        return cleaned_data
