"""
Models for trip memories: photos and journal entries.
"""
import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TripPhoto(models.Model):
    """Photo uploaded for a trip, optionally linked to an activity or itinerary item."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('trip')
    )
    activity = models.ForeignKey(
        'activities.Activity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name=_('activity'),
        help_text=_('Optional: Link this photo to a specific activity')
    )
    daily_itinerary = models.ForeignKey(
        'itinerary.DailyItinerary',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name=_('itinerary item'),
        help_text=_('Optional: Link this photo to a specific day/event')
    )
    image = models.ImageField(
        upload_to='trip_photos/%Y/%m/%d/',
        verbose_name=_('photo')
    )
    caption = models.TextField(
        blank=True,
        verbose_name=_('caption'),
        help_text=_('Optional description of the photo')
    )
    taken_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('date taken'),
        help_text=_('When was this photo taken?')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_photos',
        verbose_name=_('uploaded by')
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('uploaded at')
    )

    class Meta:
        db_table = 'trip_photos'
        verbose_name = _('trip photo')
        verbose_name_plural = _('trip photos')
        ordering = ['-taken_date', '-uploaded_at']
        indexes = [
            models.Index(fields=['trip', '-taken_date']),
            models.Index(fields=['trip', '-uploaded_at']),
            models.Index(fields=['activity']),
            models.Index(fields=['daily_itinerary']),
        ]

    def __str__(self):
        if self.caption:
            return f"{self.trip.name} - {self.caption[:50]}"
        return f"{self.trip.name} - Photo {self.uploaded_at.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        return reverse('memories:photo_detail', kwargs={'pk': self.pk})


class DailyJournal(models.Model):
    """Daily journal entry for a trip day."""

    MOOD_CHOICES = [
        (1, _('😞 Poor')),
        (2, _('😐 Fair')),
        (3, _('🙂 Good')),
        (4, _('😊 Great')),
        (5, _('🤩 Excellent')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.CASCADE,
        related_name='journal_entries',
        verbose_name=_('trip')
    )
    date = models.DateField(
        verbose_name=_('date'),
        help_text=_('Which day of the trip?')
    )
    content = models.TextField(
        verbose_name=_('journal entry'),
        help_text=_('What happened today? How was the experience?')
    )
    weather = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('weather'),
        help_text=_('Optional: Weather conditions (e.g., "Sunny, 78°F")')
    )
    mood_rating = models.PositiveSmallIntegerField(
        choices=MOOD_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('mood rating'),
        help_text=_('How was your overall mood today?')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='journal_entries',
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('created at')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('updated at')
    )

    class Meta:
        db_table = 'daily_journals'
        verbose_name = _('daily journal')
        verbose_name_plural = _('daily journals')
        ordering = ['-date']
        unique_together = [['trip', 'date', 'created_by']]  # One journal per user per day
        indexes = [
            models.Index(fields=['trip', '-date']),
            models.Index(fields=['trip', 'created_by']),
        ]

    def __str__(self):
        return f"{self.trip.name} - {self.date.strftime('%Y-%m-%d')} by {self.created_by}"

    def get_absolute_url(self):
        return reverse('memories:journal_detail', kwargs={'pk': self.pk})

    def get_mood_display_emoji(self):
        """Return just the emoji for the mood rating."""
        if self.mood_rating:
            mood_map = {1: '😞', 2: '😐', 3: '🙂', 4: '😊', 5: '🤩'}
            return mood_map.get(self.mood_rating, '')
        return ''
