"""
Django admin configuration for activities app.
"""
from django.contrib import admin
from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin interface for Activity model."""

    list_display = [
        'name',
        'trip',
        'city',
        'pre_trip_priority',
        'post_trip_rating',
        'is_favorite',
        'created_at'
    ]
    list_filter = [
        'is_favorite',
        'post_trip_rating',
        'created_at',
        'trip__status'
    ]
    search_fields = [
        'name',
        'description',
        'city',
        'trip__name',
        'trip__destination_name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('trip', 'name', 'description', 'website_url')
        }),
        ('Location', {
            'fields': (
                'address_line1',
                'address_line2',
                'city',
                'state',
                'zip_code',
                ('latitude', 'longitude'),
                ('distance_from_resort', 'travel_time_from_resort')
            )
        }),
        ('Planning Details', {
            'fields': (
                'estimated_cost',
                'estimated_duration',
                'pre_trip_priority'
            )
        }),
        ('Post-Trip Evaluation', {
            'fields': (
                'post_trip_rating',
                'is_favorite',
                'post_trip_notes'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['trip']
    ordering = ['pre_trip_priority', '-created_at']
