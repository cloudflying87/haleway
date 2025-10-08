"""
Forms for activity management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Activity


class ActivityForm(forms.ModelForm):
    """Form for creating and editing activities."""

    class Meta:
        model = Activity
        fields = [
            'name', 'description', 'website_url',
            'address_line1', 'address_line2',
            'city', 'state', 'zip_code',
            'latitude', 'longitude',
            'distance_from_resort', 'travel_time_from_resort',
            'estimated_cost', 'estimated_duration',
            'pre_trip_priority'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Snorkeling at Molokini Crater',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the activity...',
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.activity-website.com (optional)',
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address (optional)',
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apt, suite, unit, etc. (optional)',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City (optional)',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State or Province (optional)',
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zip or Postal Code (optional)',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 20.6280',
                'step': 'any',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., -156.4965',
                'step': 'any',
            }),
            'distance_from_resort': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Distance in miles (optional)',
                'step': '0.1',
            }),
            'travel_time_from_resort': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-calculated from distance',
                'readonly': 'readonly',
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cost per person (optional)',
                'step': '0.01',
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Duration in minutes (optional)',
            }),
            'pre_trip_priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0 = unranked, lower = higher priority',
            }),
        }


class ActivityRatingForm(forms.ModelForm):
    """Form for rating activities after a trip."""

    class Meta:
        model = Activity
        fields = ['post_trip_rating', 'is_favorite', 'post_trip_notes']
        widgets = {
            'post_trip_rating': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'rating-input'}
            ),
            'is_favorite': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'post_trip_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience, tips, or thoughts...',
            }),
        }
        labels = {
            'post_trip_rating': _('How would you rate this activity?'),
            'is_favorite': _('Would you do this again?'),
            'post_trip_notes': _('Post-trip notes'),
        }
