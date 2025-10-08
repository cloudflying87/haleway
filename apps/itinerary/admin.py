"""
Django admin configuration for itinerary app.
"""
from django.contrib import admin
from .models import DailyItinerary


@admin.register(DailyItinerary)
class DailyItineraryAdmin(admin.ModelAdmin):
    """Admin interface for DailyItinerary model."""

    list_display = [
        'get_display_title',
        'trip',
        'date',
        'time_start',
        'time_end',
        'activity',
        'order',
        'created_at'
    ]
    list_filter = [
        'date',
        'trip__status',
        'created_at'
    ]
    search_fields = [
        'title',
        'notes',
        'trip__name',
        'trip__destination_name',
        'activity__name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('trip', 'date', 'activity', 'title', 'notes')
        }),
        ('Timing', {
            'fields': ('time_start', 'time_end', 'order')
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['trip', 'activity']
    ordering = ['date', 'time_start', 'order']
    date_hierarchy = 'date'

    def get_display_title(self, obj):
        """Display title in list view."""
        return obj.get_display_title()
    get_display_title.short_description = 'Title'
