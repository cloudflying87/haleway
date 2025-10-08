"""
Note and NoteCategory models for HaleWay.
Manages categorized notes with full-text search support.
"""

import uuid

import structlog
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

logger = structlog.get_logger(__name__)


class NoteCategory(models.Model):
    """
    Represents a category for organizing notes within a trip.
    """

    # Color choices for UI organization
    COLOR_CHOICES = [
        ("#2E86AB", _("Ocean Blue")),
        ("#FF6B6B", _("Sunset Coral")),
        ("#06A77D", _("Palm Green")),
        ("#F4E8C1", _("Sandy Beige")),
        ("#9B59B6", _("Purple")),
        ("#E67E22", _("Orange")),
        ("#3498DB", _("Sky Blue")),
        ("#E74C3C", _("Red")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="note_categories",
        verbose_name=_("trip"),
    )
    name = models.CharField(
        _("category name"),
        max_length=100,
        help_text=_("e.g., Transportation, Food Restrictions, Emergency Contacts"),
    )
    color_code = models.CharField(
        _("color"),
        max_length=7,
        choices=COLOR_CHOICES,
        default="#2E86AB",
        help_text=_("Hex color for UI organization"),
    )
    order = models.PositiveIntegerField(
        _("display order"), default=0, help_text=_("Lower numbers appear first")
    )

    class Meta:
        verbose_name = _("note category")
        verbose_name_plural = _("note categories")
        db_table = "note_categories"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["trip", "order"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["trip", "name"], name="unique_category_per_trip")
        ]

    def __str__(self):
        return f"{self.name} ({self.trip.name})"

    def get_absolute_url(self):
        """Return the URL for managing this category."""
        return reverse("notes:category_update", kwargs={"pk": self.pk})


class Note(models.Model):
    """
    Represents a note within a trip, optionally categorized.
    Supports full-text search on title and content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="notes", verbose_name=_("trip")
    )
    category = models.ForeignKey(
        NoteCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
        verbose_name=_("category"),
    )
    title = models.CharField(_("title"), max_length=200)
    content = models.TextField(_("content"))
    is_pinned = models.BooleanField(
        _("pinned"), default=False, help_text=_("Pin important notes to the top")
    )

    # Search vector for full-text search
    search_vector = SearchVectorField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_notes",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("note")
        verbose_name_plural = _("notes")
        db_table = "notes"
        ordering = ["-is_pinned", "-updated_at"]
        indexes = [
            models.Index(fields=["trip", "category"]),
            models.Index(fields=["trip", "is_pinned"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.trip.name}"

    def get_absolute_url(self):
        """Return the URL for this note's detail page."""
        return reverse("notes:note_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        """Override save to log note creation/updates."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            logger.info(
                "note_created",
                note_id=str(self.id),
                trip_id=str(self.trip_id),
                created_by=self.created_by.username if self.created_by else None,
                is_pinned=self.is_pinned,
            )
        else:
            logger.info(
                "note_updated",
                note_id=str(self.id),
                trip_id=str(self.trip_id),
                is_pinned=self.is_pinned,
            )
