"""
Forms for trip memories.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import DailyJournal, TripPhoto


class TripPhotoForm(forms.ModelForm):
    """Form for uploading trip photos."""

    class Meta:
        model = TripPhoto
        fields = ["image", "caption", "taken_date", "activity", "daily_itinerary"]
        widgets = {
            "caption": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Describe this photo...", "class": "form-control"}
            ),
            "taken_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "image": forms.FileInput(attrs={"accept": "image/*", "class": "form-control"}),
            "activity": forms.Select(attrs={"class": "form-control"}),
            "daily_itinerary": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, trip=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

        # Filter activity and itinerary choices to only those for this trip
        if trip:
            self.fields["activity"].queryset = trip.activities.all().order_by("name")
            self.fields["activity"].empty_label = "None (general trip photo)"

            self.fields["daily_itinerary"].queryset = trip.itinerary_items.all().order_by(
                "date", "time_start"
            )
            self.fields["daily_itinerary"].empty_label = "None (general trip photo)"
            self.fields["daily_itinerary"].label_from_instance = (
                lambda obj: f"{obj.date.strftime('%b %d')} - {obj.get_display_title()}"
            )

        # Make fields optional
        self.fields["caption"].required = False
        self.fields["taken_date"].required = False
        self.fields["activity"].required = False
        self.fields["daily_itinerary"].required = False

    def clean_taken_date(self):
        """Validate that taken_date falls within trip dates."""
        taken_date = self.cleaned_data.get("taken_date")
        if taken_date and self.trip:
            if taken_date < self.trip.start_date or taken_date > self.trip.end_date:
                raise ValidationError(
                    _("Photo date must be between trip start (%(start)s) and end (%(end)s)."),
                    params={
                        "start": self.trip.start_date.strftime("%Y-%m-%d"),
                        "end": self.trip.end_date.strftime("%Y-%m-%d"),
                    },
                )
        return taken_date

    def clean(self):
        """Validate that activity and itinerary don't conflict."""
        cleaned_data = super().clean()
        activity = cleaned_data.get("activity")
        daily_itinerary = cleaned_data.get("daily_itinerary")

        # If both are set, warn that daily_itinerary takes precedence
        if activity and daily_itinerary:
            if daily_itinerary.activity != activity:
                self.add_error(
                    "daily_itinerary",
                    _("This itinerary item is for a different activity. Choose one or the other."),
                )

        return cleaned_data


class QuickPhotoUploadForm(forms.ModelForm):
    """Simplified form for quick photo upload without linking."""

    class Meta:
        model = TripPhoto
        fields = ["image", "caption", "taken_date"]
        widgets = {
            "caption": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Optional caption...", "class": "form-control"}
            ),
            "taken_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "image": forms.FileInput(attrs={"accept": "image/*", "class": "form-control"}),
        }

    def __init__(self, trip=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.fields["caption"].required = False
        self.fields["taken_date"].required = False


class DailyJournalForm(forms.ModelForm):
    """Form for daily journal entries."""

    class Meta:
        model = DailyJournal
        fields = ["date", "content", "weather", "mood_rating"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "content": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": "What happened today? What did you see, do, eat? How did it make you feel?",
                    "class": "form-control",
                }
            ),
            "weather": forms.TextInput(
                attrs={"placeholder": "e.g., Sunny, 78°F", "class": "form-control"}
            ),
            "mood_rating": forms.RadioSelect(attrs={"class": "mood-rating-radio"}),
        }

    def __init__(self, trip=None, created_by=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip
        self.created_by = created_by

        # Make weather optional
        self.fields["weather"].required = False
        self.fields["mood_rating"].required = False

    def clean_date(self):
        """Validate that date falls within trip dates and no duplicate exists."""
        date = self.cleaned_data.get("date")
        if date and self.trip:
            # Check date is within trip range
            if date < self.trip.start_date or date > self.trip.end_date:
                raise ValidationError(
                    _("Journal date must be between trip start (%(start)s) and end (%(end)s)."),
                    params={
                        "start": self.trip.start_date.strftime("%Y-%m-%d"),
                        "end": self.trip.end_date.strftime("%Y-%m-%d"),
                    },
                )

            # Check for duplicate (only on create, not edit)
            if self.created_by and not self.instance.pk:
                existing = DailyJournal.objects.filter(
                    trip=self.trip, date=date, created_by=self.created_by
                ).exists()
                if existing:
                    raise ValidationError(
                        _("You already have a journal entry for %(date)s. Edit it instead."),
                        params={"date": date.strftime("%B %d, %Y")},
                    )

        return date
