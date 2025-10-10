"""
Trip and Resort models for HaleWay.
Manages trip planning and resort details.
"""

import uuid

import structlog
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

logger = structlog.get_logger(__name__)


class Trip(models.Model):
    """
    Represents a vacation trip planned by a family.
    """

    STATUS_CHOICES = [
        ("dream", _("Dream Trip")),
        ("planning", _("Planning")),
        ("active", _("Active")),
        ("completed", _("Completed")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        "families.Family", on_delete=models.CASCADE, related_name="trips", verbose_name=_("family")
    )
    name = models.CharField(_("trip name"), max_length=200, help_text=_("e.g., Hawaii 2025"))
    destination_name = models.CharField(
        _("destination"), max_length=200, help_text=_("e.g., Maui, Hawaii")
    )
    start_date = models.DateField(
        _("start date"), null=True, blank=True, help_text=_("Optional for dream trips")
    )
    end_date = models.DateField(
        _("end date"), null=True, blank=True, help_text=_("Optional for dream trips")
    )
    status = models.CharField(
        _("status"), max_length=10, choices=STATUS_CHOICES, default="planning"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_trips",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("trip")
        verbose_name_plural = _("trips")
        db_table = "trips"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["family", "status"]),
            models.Index(fields=["start_date"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.destination_name}"

    def get_absolute_url(self):
        """Return the URL for this trip's detail page."""
        return reverse("trips:trip_detail", kwargs={"pk": self.pk})

    def duration_days(self):
        """Calculate trip duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def is_upcoming(self):
        """Check if the trip is in the future."""
        from django.utils import timezone

        return self.start_date > timezone.now().date()

    def is_active(self):
        """Check if the trip is currently happening."""
        from django.utils import timezone

        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def is_past(self):
        """Check if the trip has already happened."""
        from django.utils import timezone

        return self.end_date < timezone.now().date()


class Resort(models.Model):
    """
    Represents lodging/resort details for a trip.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.OneToOneField(
        Trip, on_delete=models.CASCADE, related_name="resort", verbose_name=_("trip")
    )
    name = models.CharField(_("resort name"), max_length=200)
    website_url = models.URLField(_("website"), blank=True)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)

    # Check-in/Check-out times
    check_in_time = models.TimeField(
        _("check-in time"),
        null=True,
        blank=True,
        help_text=_("Typical check-in time (e.g., 3:00 PM)"),
    )
    check_out_time = models.TimeField(
        _("check-out time"),
        null=True,
        blank=True,
        help_text=_("Typical check-out time (e.g., 11:00 AM)"),
    )

    # Address fields
    address_line1 = models.CharField(_("address line 1"), max_length=200, blank=True)
    address_line2 = models.CharField(_("address line 2"), max_length=200, blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True)
    state = models.CharField(_("state/province"), max_length=100, blank=True)
    zip_code = models.CharField(_("zip/postal code"), max_length=20, blank=True)
    country = models.CharField(_("country"), max_length=100, default="USA")

    # Location coordinates (for future distance calculations)
    latitude = models.DecimalField(
        _("latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_("For future distance calculations"),
    )
    longitude = models.DecimalField(
        _("longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_("For future distance calculations"),
    )

    # General notes
    general_notes = models.TextField(
        _("notes"),
        blank=True,
        help_text=_("Confirmation numbers, check-in info, parking details, etc."),
    )

    class Meta:
        verbose_name = _("resort")
        verbose_name_plural = _("resorts")
        db_table = "resorts"

    def __str__(self):
        return f"{self.name} - {self.trip.name}"

    def get_full_address(self):
        """Return formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.zip_code}".strip(),
            self.country,
        ]
        return ", ".join(filter(None, parts))


class TripResortOption(models.Model):
    """
    Represents a potential resort option for a dream trip.
    Allows comparing multiple resorts before finalizing trip plans.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="resort_options", verbose_name=_("trip")
    )
    name = models.CharField(_("resort name"), max_length=200)
    website_url = models.URLField(_("website"), blank=True)
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)

    # Address fields
    address_line1 = models.CharField(_("address line 1"), max_length=200, blank=True)
    address_line2 = models.CharField(_("address line 2"), max_length=200, blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True)
    state = models.CharField(_("state/province"), max_length=100, blank=True)
    zip_code = models.CharField(_("zip/postal code"), max_length=20, blank=True)
    country = models.CharField(_("country"), max_length=100, default="USA")

    # Location coordinates
    latitude = models.DecimalField(
        _("latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        _("longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Comparison fields
    estimated_cost_per_night = models.DecimalField(
        _("estimated cost per night"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    pros = models.TextField(_("pros"), blank=True, help_text=_("What's good about this resort"))
    cons = models.TextField(_("cons"), blank=True, help_text=_("Concerns or drawbacks"))
    rating = models.IntegerField(
        _("rating"),
        null=True,
        blank=True,
        help_text=_("Preliminary rating (1-5)"),
        choices=[(i, str(i)) for i in range(1, 6)],
    )
    is_preferred = models.BooleanField(
        _("preferred option"), default=False, help_text=_("Mark as favorite option")
    )
    order = models.IntegerField(_("display order"), default=0)

    # General notes
    general_notes = models.TextField(_("notes"), blank=True)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("resort option")
        verbose_name_plural = _("resort options")
        db_table = "trip_resort_options"
        ordering = ["order", "-is_preferred", "name"]
        indexes = [
            models.Index(fields=["trip", "order"]),
            models.Index(fields=["trip", "is_preferred"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.trip.name}"

    def get_full_address(self):
        """Return formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.zip_code}".strip(),
            self.country,
        ]
        return ", ".join(filter(None, parts))


class ResortWishlist(models.Model):
    """
    Family-level wishlist of resorts to consider for future trips.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        "families.Family",
        on_delete=models.CASCADE,
        related_name="resort_wishlist",
        verbose_name=_("family"),
    )
    name = models.CharField(_("resort name"), max_length=200)
    destination = models.CharField(
        _("destination"),
        max_length=200,
        help_text=_("e.g., Maui, Paris, Tokyo"),
    )
    website_url = models.URLField(_("website"), blank=True)

    # Address fields
    address_line1 = models.CharField(_("address line 1"), max_length=200, blank=True)
    address_line2 = models.CharField(_("address line 2"), max_length=200, blank=True)
    city = models.CharField(_("city"), max_length=100, blank=True)
    state = models.CharField(_("state/province"), max_length=100, blank=True)
    zip_code = models.CharField(_("zip/postal code"), max_length=20, blank=True)
    country = models.CharField(_("country"), max_length=100, default="USA")

    # Location coordinates
    latitude = models.DecimalField(
        _("latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        _("longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # Wishlist fields
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Why we want to visit this resort"),
    )
    estimated_cost_per_night = models.DecimalField(
        _("estimated cost per night"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    tags = models.CharField(
        _("tags"),
        max_length=500,
        blank=True,
        help_text=_("Comma-separated tags: beach, luxury, family-friendly, all-inclusive"),
    )
    notes = models.TextField(_("notes"), blank=True, help_text=_("Research notes, recommendations"))

    # Tracking
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="added_resorts",
        verbose_name=_("added by"),
    )
    is_favorite = models.BooleanField(_("favorite"), default=False)
    visited = models.BooleanField(_("visited"), default=False)
    visited_trip = models.ForeignKey(
        Trip,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visited_resorts",
        verbose_name=_("visited on trip"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("resort wishlist item")
        verbose_name_plural = _("resort wishlist")
        db_table = "resort_wishlist"
        ordering = ["-is_favorite", "destination", "name"]
        indexes = [
            models.Index(fields=["family", "is_favorite"]),
            models.Index(fields=["family", "visited"]),
            models.Index(fields=["family", "destination"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.destination}"

    def get_full_address(self):
        """Return formatted full address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.zip_code}".strip(),
            self.country,
        ]
        return ", ".join(filter(None, parts))

    def get_tags_list(self):
        """Return tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",")]
        return []
