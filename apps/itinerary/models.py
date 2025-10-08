"""
Daily itinerary models for HaleWay.
Manages daily schedules and activity assignments for trips.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import structlog

logger = structlog.get_logger(__name__)


class DailyItinerary(models.Model):
    """
    Represents a scheduled item on a specific day of a trip.
    Can be linked to an Activity or be a standalone event.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.CASCADE,
        related_name='itinerary_items',
        verbose_name=_('trip')
    )
    activity = models.ForeignKey(
        'activities.Activity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itinerary_items',
        verbose_name=_('activity'),
        help_text=_('Link to an activity (optional for standalone events)')
    )
    date = models.DateField(_('date'), help_text=_('Day of the trip'))
    time_start = models.TimeField(
        _('start time'),
        null=True,
        blank=True,
        help_text=_('Start time (optional)')
    )
    time_end = models.TimeField(
        _('end time'),
        null=True,
        blank=True,
        help_text=_('End time (optional)')
    )
    title = models.CharField(
        _('title'),
        max_length=200,
        blank=True,
        help_text=_('For standalone events like "Breakfast" or "Check-in"')
    )
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Additional notes or details')
    )
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
        help_text=_('Display order for items on the same day')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_itinerary_items',
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('daily itinerary item')
        verbose_name_plural = _('daily itinerary items')
        db_table = 'daily_itinerary'
        ordering = ['date', 'time_start', 'order']
        indexes = [
            models.Index(fields=['trip', 'date']),
            models.Index(fields=['trip', 'date', 'order']),
            models.Index(fields=['activity']),
        ]

    def __str__(self):
        if self.activity:
            return f"{self.activity.name} - {self.date}"
        return f"{self.title} - {self.date}"

    def get_absolute_url(self):
        """Return the URL for the day view containing this item."""
        return reverse('itinerary:day_detail', kwargs={
            'trip_pk': self.trip.pk,
            'date': self.date.isoformat()
        })

    def get_display_title(self):
        """Return the title to display (activity name or custom title)."""
        if self.activity:
            return self.activity.name
        return self.title

    def get_time_display(self):
        """Return formatted time range."""
        if self.time_start and self.time_end:
            return f"{self.time_start.strftime('%I:%M %p')} - {self.time_end.strftime('%I:%M %p')}"
        elif self.time_start:
            return f"{self.time_start.strftime('%I:%M %p')}"
        return "All day"

    def is_all_day(self):
        """Check if this is an all-day event."""
        return not self.time_start and not self.time_end

    def clean(self):
        """Validate the itinerary item."""
        from django.core.exceptions import ValidationError

        # Must have either activity or title
        if not self.activity and not self.title:
            raise ValidationError(_('Must specify either an activity or a custom title.'))

        # If activity is set, title should be empty (we'll use activity name)
        if self.activity and self.title:
            raise ValidationError(_('Cannot specify both activity and custom title.'))

        # Validate date is within trip dates
        if self.trip:
            if self.date < self.trip.start_date or self.date > self.trip.end_date:
                raise ValidationError(_(
                    f'Date must be within trip dates '
                    f'({self.trip.start_date} to {self.trip.end_date})'
                ))

        # Validate time range
        if self.time_start and self.time_end:
            if self.time_end <= self.time_start:
                raise ValidationError(_('End time must be after start time.'))
