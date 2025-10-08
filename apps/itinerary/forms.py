"""
Forms for itinerary management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import DailyItinerary


class ItineraryItemForm(forms.ModelForm):
    """Form for creating/editing itinerary items."""

    class Meta:
        model = DailyItinerary
        fields = [
            'date', 'activity', 'title', 'time_start', 'time_end', 'notes', 'order'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'activity': forms.Select(attrs={
                'class': 'form-control',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Breakfast, Check-in, Free time',
            }),
            'time_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'time_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional details or reminders...',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display order (lower = earlier)',
            }),
        }

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

        # Filter activities to only those for this trip
        if trip:
            self.fields['activity'].queryset = trip.activities.all()
            self.fields['activity'].empty_label = "-- Select an activity or add custom event --"

            # Set date limits based on trip dates
            self.fields['date'].widget.attrs.update({
                'min': trip.start_date.isoformat(),
                'max': trip.end_date.isoformat(),
            })

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        activity = cleaned_data.get('activity')
        title = cleaned_data.get('title')
        date = cleaned_data.get('date')
        time_start = cleaned_data.get('time_start')
        time_end = cleaned_data.get('time_end')

        # Must have either activity or title
        if not activity and not title:
            raise ValidationError(_('Please select an activity or enter a custom event title.'))

        # Cannot have both
        if activity and title:
            raise ValidationError(_('Please choose either an activity OR a custom event, not both.'))

        # Validate date is within trip dates
        if date and self.trip:
            if date < self.trip.start_date or date > self.trip.end_date:
                raise ValidationError({
                    'date': _(f'Date must be between {self.trip.start_date} and {self.trip.end_date}')
                })

        # Validate time range
        if time_start and time_end:
            if time_end <= time_start:
                raise ValidationError({
                    'time_end': _('End time must be after start time.')
                })

        return cleaned_data


class QuickAddEventForm(forms.Form):
    """Quick form for adding non-activity events."""

    title = forms.CharField(
        max_length=200,
        label=_('Event Title'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Breakfast at hotel',
        })
    )
    date = forms.DateField(
        label=_('Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    time_start = forms.TimeField(
        required=False,
        label=_('Start Time (optional)'),
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
        })
    )
    time_end = forms.TimeField(
        required=False,
        label=_('End Time (optional)'),
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
        })
    )
    notes = forms.CharField(
        required=False,
        label=_('Notes'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes...',
        })
    )

    def __init__(self, *args, trip=None, date=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

        if trip:
            self.fields['date'].widget.attrs.update({
                'min': trip.start_date.isoformat(),
                'max': trip.end_date.isoformat(),
            })

        # Pre-fill date if provided
        if date:
            self.initial['date'] = date

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_start = cleaned_data.get('time_start')
        time_end = cleaned_data.get('time_end')

        # Validate date is within trip dates
        if date and self.trip:
            if date < self.trip.start_date or date > self.trip.end_date:
                raise ValidationError({
                    'date': _(f'Date must be between {self.trip.start_date} and {self.trip.end_date}')
                })

        # Validate time range
        if time_start and time_end:
            if time_end <= time_start:
                raise ValidationError({
                    'time_end': _('End time must be after start time.')
                })

        return cleaned_data


class AssignActivityForm(forms.Form):
    """Form for assigning an existing activity to a day/time."""

    date = forms.DateField(
        label=_('Date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    time_start = forms.TimeField(
        required=False,
        label=_('Start Time (optional)'),
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
        })
    )
    time_end = forms.TimeField(
        required=False,
        label=_('End Time (optional)'),
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
        })
    )
    notes = forms.CharField(
        required=False,
        label=_('Notes for this day'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any specific notes for this scheduled activity...',
        })
    )

    def __init__(self, *args, trip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

        if trip:
            self.fields['date'].widget.attrs.update({
                'min': trip.start_date.isoformat(),
                'max': trip.end_date.isoformat(),
            })

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_start = cleaned_data.get('time_start')
        time_end = cleaned_data.get('time_end')

        # Validate date is within trip dates
        if date and self.trip:
            if date < self.trip.start_date or date > self.trip.end_date:
                raise ValidationError({
                    'date': _(f'Date must be between {self.trip.start_date} and {self.trip.end_date}')
                })

        # Validate time range
        if time_start and time_end:
            if time_end <= time_start:
                raise ValidationError({
                    'time_end': _('End time must be after start time.')
                })

        return cleaned_data
