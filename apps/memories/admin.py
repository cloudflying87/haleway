"""
Django admin configuration for memories app.
"""

from django.contrib import admin

from .models import DailyJournal, TripPhoto


@admin.register(TripPhoto)
class TripPhotoAdmin(admin.ModelAdmin):
    """Admin interface for TripPhoto model."""

    list_display = [
        "trip",
        "caption_preview",
        "taken_date",
        "uploaded_by",
        "uploaded_at",
        "activity",
        "daily_itinerary",
    ]
    list_filter = ["taken_date", "uploaded_at", "trip__status"]
    search_fields = ["caption", "trip__name", "activity__name", "uploaded_by__email"]
    readonly_fields = ["id", "uploaded_at"]
    fieldsets = (
        ("Photo", {"fields": ("image", "caption", "taken_date")}),
        ("Trip Information", {"fields": ("trip", "activity", "daily_itinerary")}),
        ("Metadata", {"fields": ("id", "uploaded_by", "uploaded_at"), "classes": ("collapse",)}),
    )
    autocomplete_fields = ["trip", "activity", "daily_itinerary"]
    ordering = ["-uploaded_at"]

    @admin.display(description="Caption")
    def caption_preview(self, obj):
        """Return truncated caption for list display."""
        if obj.caption:
            return obj.caption[:50] + ("..." if len(obj.caption) > 50 else "")
        return "(no caption)"


@admin.register(DailyJournal)
class DailyJournalAdmin(admin.ModelAdmin):
    """Admin interface for DailyJournal model."""

    list_display = ["trip", "date", "mood_rating", "weather", "created_by", "created_at"]
    list_filter = ["date", "mood_rating", "created_at", "trip__status"]
    search_fields = ["content", "trip__name", "created_by__email", "weather"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Journal Entry", {"fields": ("trip", "date", "content")}),
        ("Details", {"fields": ("weather", "mood_rating")}),
        (
            "Metadata",
            {"fields": ("id", "created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    autocomplete_fields = ["trip"]
    ordering = ["-date"]
