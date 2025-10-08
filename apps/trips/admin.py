"""
Django admin configuration for trips app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Resort, Trip


class ResortInline(admin.StackedInline):
    """Inline admin for resort details."""

    model = Resort
    extra = 0
    fieldsets = (
        ("Basic Information", {"fields": ("name", "website_url")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        ("Notes", {"fields": ("general_notes",)}),
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Admin interface for Trip model."""

    list_display = [
        "name",
        "destination_name",
        "family",
        "start_date",
        "end_date",
        "duration",
        "status",
        "status_badge",
    ]
    list_filter = ["status", "start_date", "created_at"]
    search_fields = ["name", "destination_name", "family__name"]
    readonly_fields = ["id", "created_at", "updated_at", "duration"]
    inlines = [ResortInline]

    fieldsets = (
        ("Trip Details", {"fields": ("family", "name", "destination_name", "status")}),
        ("Dates", {"fields": ("start_date", "end_date", "duration")}),
        (
            "Metadata",
            {"fields": ("id", "created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Duration")
    def duration(self, obj):
        """Display trip duration."""
        return f"{obj.duration_days()} days"

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Display a colored status badge."""
        colors = {"planning": "#ffc107", "active": "#28a745", "completed": "#6c757d"}
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(Resort)
class ResortAdmin(admin.ModelAdmin):
    """Admin interface for Resort model."""

    list_display = ["name", "trip", "city", "state", "country"]
    list_filter = ["country", "state"]
    search_fields = ["name", "city", "trip__name"]
    readonly_fields = ["id"]

    fieldsets = (
        ("Basic Information", {"fields": ("trip", "name", "website_url")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        ("Notes", {"fields": ("general_notes",)}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )
