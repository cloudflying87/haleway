"""
Activity models for HaleWay.
Manages activities and attractions for trips.
"""
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import structlog

logger = structlog.get_logger(__name__)


class Activity(models.Model):
    """
    Represents an activity or attraction for a trip.
    Can be prioritized before the trip and rated after.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('trip')
    )
    name = models.CharField(_('activity name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    website_url = models.URLField(_('website'), blank=True)

    # Address fields
    address_line1 = models.CharField(_('address line 1'), max_length=200, blank=True)
    address_line2 = models.CharField(_('address line 2'), max_length=200, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state/province'), max_length=100, blank=True)
    zip_code = models.CharField(_('zip/postal code'), max_length=20, blank=True)

    # Location coordinates (for future automatic distance calculations)
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('For future automatic distance calculations')
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('For future automatic distance calculations')
    )

    # Distance and travel time from resort
    distance_from_resort = models.DecimalField(
        _('distance from resort (miles)'),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Distance from resort in miles (auto-calculated if address provided)')
    )
    travel_time_from_resort = models.PositiveIntegerField(
        _('travel time from resort (minutes)'),
        null=True,
        blank=True,
        help_text=_('Estimated driving time from resort (auto-calculated from distance)')
    )

    # Cost and time estimates
    estimated_cost = models.DecimalField(
        _('estimated cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Estimated cost per person')
    )
    estimated_duration = models.PositiveIntegerField(
        _('estimated duration (minutes)'),
        null=True,
        blank=True,
        help_text=_('How long the activity takes')
    )

    # Pre-trip planning
    pre_trip_priority = models.PositiveIntegerField(
        _('priority'),
        default=0,
        help_text=_('Lower numbers = higher priority. 0 = unranked')
    )

    # Post-trip evaluation
    post_trip_rating = models.PositiveIntegerField(
        _('rating'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rate 1-5 stars after the trip')
    )
    post_trip_notes = models.TextField(
        _('post-trip notes'),
        blank=True,
        help_text=_('Reflections, tips, or notes after visiting')
    )
    is_favorite = models.BooleanField(
        _('favorite'),
        default=False,
        help_text=_('Flag activities you would do again')
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_activities',
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')
        db_table = 'activities'
        ordering = ['pre_trip_priority', '-created_at']
        indexes = [
            models.Index(fields=['trip', 'pre_trip_priority']),
            models.Index(fields=['trip', 'post_trip_rating']),
            models.Index(fields=['trip', 'is_favorite']),
        ]

    def __str__(self):
        return f"{self.name} - {self.trip.name}"

    def get_absolute_url(self):
        """Return the URL for this activity's detail page."""
        return reverse('activities:activity_detail', kwargs={'pk': self.pk})

    def get_full_address(self):
        """Return formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.zip_code}".strip(),
        ]
        return ', '.join(filter(None, parts))

    def has_rating(self):
        """Check if activity has been rated."""
        return self.post_trip_rating is not None

    def get_duration_display(self):
        """Return human-readable duration."""
        if not self.estimated_duration:
            return "Unknown"

        hours = self.estimated_duration // 60
        minutes = self.estimated_duration % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"

    def get_travel_time_display(self):
        """Return human-readable travel time from resort."""
        if not self.travel_time_from_resort:
            return "Unknown"

        hours = self.travel_time_from_resort // 60
        minutes = self.travel_time_from_resort % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
