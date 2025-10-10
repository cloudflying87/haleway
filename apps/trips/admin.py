"""
Django admin configuration for trips app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Resort, ResortWishlist, Trip, TripResortOption


class ResortInline(admin.StackedInline):
    """Inline admin for resort details."""

    model = Resort
    extra = 0
    fieldsets = (
        ("Basic Information", {"fields": ("name", "website_url", "phone_number")}),
        ("Check-in/Check-out", {"fields": ("check_in_time", "check_out_time")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        ("Notes", {"fields": ("general_notes",)}),
    )


class TripResortOptionInline(admin.TabularInline):
    """Inline admin for resort options on dream trips."""

    model = TripResortOption
    extra = 1
    fields = ["name", "city", "state", "rating", "is_preferred", "order"]
    ordering = ["order", "-is_preferred"]


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
    inlines = [ResortInline, TripResortOptionInline]

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
        colors = {
            "dream": "#e91e63",  # Pink for dream trips
            "planning": "#ffc107",  # Yellow for planning
            "active": "#28a745",  # Green for active
            "completed": "#6c757d",  # Gray for completed
        }
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
        ("Basic Information", {"fields": ("trip", "name", "website_url", "phone_number")}),
        ("Check-in/Check-out", {"fields": ("check_in_time", "check_out_time")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        ("Notes", {"fields": ("general_notes",)}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )


@admin.register(TripResortOption)
class TripResortOptionAdmin(admin.ModelAdmin):
    """Admin interface for TripResortOption model."""

    list_display = ["name", "trip", "city", "state", "rating", "is_preferred", "order"]
    list_filter = ["is_preferred", "rating", "trip__status"]
    search_fields = ["name", "city", "trip__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("trip", "name", "website_url", "phone_number")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        (
            "Comparison Details",
            {
                "fields": (
                    "estimated_cost_per_night",
                    "rating",
                    "is_preferred",
                    "order",
                    "pros",
                    "cons",
                )
            },
        ),
        ("Notes", {"fields": ("general_notes",)}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ResortWishlist)
class ResortWishlistAdmin(admin.ModelAdmin):
    """Admin interface for ResortWishlist model."""

    list_display = [
        "name",
        "destination",
        "family",
        "is_favorite",
        "visited",
        "added_by",
        "created_at",
    ]
    list_filter = ["is_favorite", "visited", "country", "created_at"]
    search_fields = ["name", "destination", "city", "description", "tags"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("family", "name", "destination", "website_url")}),
        (
            "Address",
            {"fields": ("address_line1", "address_line2", "city", "state", "zip_code", "country")},
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        (
            "Wishlist Details",
            {
                "fields": (
                    "description",
                    "estimated_cost_per_night",
                    "tags",
                    "is_favorite",
                )
            },
        ),
        ("Visit Tracking", {"fields": ("visited", "visited_trip")}),
        ("Notes", {"fields": ("notes",)}),
        (
            "Metadata",
            {"fields": ("id", "added_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
