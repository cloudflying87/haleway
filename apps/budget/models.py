"""
Budget models for HaleWay.
Manages budget categories and items for trip expense tracking.
"""

import uuid
from decimal import Decimal

import structlog
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

logger = structlog.get_logger(__name__)


class BudgetCategory(models.Model):
    """
    Represents a budget category for organizing expenses within a trip.
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
        related_name="budget_categories",
        verbose_name=_("trip"),
    )
    name = models.CharField(
        _("category name"),
        max_length=100,
        help_text=_("e.g., Lodging, Food, Activities, Transportation"),
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
        verbose_name = _("budget category")
        verbose_name_plural = _("budget categories")
        db_table = "budget_categories"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["trip", "order"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["trip", "name"], name="unique_budget_category_per_trip")
        ]

    def __str__(self):
        return f"{self.name} ({self.trip.name})"

    def get_absolute_url(self):
        """Return the URL for managing this category."""
        return reverse("budget:category_update", kwargs={"pk": self.pk})

    def get_total_estimated(self):
        """Calculate total estimated amount for this category."""
        return self.items.aggregate(total=models.Sum("estimated_amount"))["total"] or Decimal(
            "0.00"
        )

    def get_total_actual(self):
        """Calculate total actual amount for this category."""
        return self.items.aggregate(total=models.Sum("actual_amount"))["total"] or Decimal("0.00")


class BudgetItem(models.Model):
    """
    Represents a budget item (expense) within a trip.
    Tracks estimated vs actual costs and payment information.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="budget_items", verbose_name=_("trip")
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name=_("category"),
    )
    description = models.CharField(
        _("description"), max_length=200, help_text=_("Brief description of the expense")
    )
    estimated_amount = models.DecimalField(
        _("estimated amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Estimated cost in USD"),
    )
    actual_amount = models.DecimalField(
        _("actual amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Actual cost in USD (leave blank until paid)"),
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="budget_items_paid",
        verbose_name=_("paid by"),
    )
    payment_date = models.DateField(
        _("payment date"), null=True, blank=True, help_text=_("Date when payment was made")
    )
    notes = models.TextField(
        _("notes"), blank=True, help_text=_("Additional notes about this expense")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_budget_items",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("budget item")
        verbose_name_plural = _("budget items")
        db_table = "budget_items"
        ordering = ["category__order", "category__name", "-created_at"]
        indexes = [
            models.Index(fields=["trip", "category"]),
            models.Index(fields=["trip", "paid_by"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"{self.description} - {self.trip.name}"

    def get_absolute_url(self):
        """Return the URL for this budget item's detail page."""
        return reverse("budget:item_detail", kwargs={"pk": self.pk})

    @property
    def is_paid(self):
        """Check if this item has been paid."""
        return self.actual_amount is not None

    @property
    def variance(self):
        """Calculate variance between estimated and actual (negative = over budget)."""
        if self.actual_amount is None:
            return None
        return self.estimated_amount - self.actual_amount

    @property
    def variance_percentage(self):
        """Calculate variance as a percentage of estimated."""
        if self.actual_amount is None or self.estimated_amount == 0:
            return None
        return (self.variance / self.estimated_amount) * 100

    def save(self, *args, **kwargs):
        """Override save to log budget item creation/updates."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            logger.info(
                "budget_item_created",
                item_id=str(self.id),
                trip_id=str(self.trip_id),
                category=self.category.name if self.category else None,
                estimated_amount=float(self.estimated_amount),
                created_by=self.created_by.username if self.created_by else None,
            )
        else:
            logger.info(
                "budget_item_updated",
                item_id=str(self.id),
                trip_id=str(self.trip_id),
                is_paid=self.is_paid,
                actual_amount=float(self.actual_amount) if self.actual_amount else None,
            )
