"""
Packing list models for HaleWay.
Manages reusable packing templates and trip-specific packing lists.
"""

import uuid

import structlog
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

logger = structlog.get_logger(__name__)


class PackingListTemplate(models.Model):
    """
    Reusable packing list template (e.g., Beach, Mountains, Summer, Winter).
    Can be system-provided or user-created.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("template name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    is_system_template = models.BooleanField(
        _("system template"), default=False, help_text=_("Built-in template that cannot be deleted")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_packing_templates",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("packing list template")
        verbose_name_plural = _("packing list templates")
        db_table = "packing_list_templates"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the URL for this template's detail page."""
        return reverse("packing:template_detail", kwargs={"pk": self.pk})

    def duplicate_for_trip(self, trip, assigned_to=None, list_name=None):
        """
        Create a trip-specific packing list from this template.

        Args:
            trip: The Trip instance to create the list for
            assigned_to: Optional User to assign the list to
            list_name: Optional custom name for the list

        Returns:
            TripPackingList instance
        """
        # Create the trip packing list
        packing_list = TripPackingList.objects.create(
            trip=trip, name=list_name or self.name, based_on_template=self, assigned_to=assigned_to
        )

        # Copy all template items
        for template_item in self.items.all():
            TripPackingItem.objects.create(
                packing_list=packing_list,
                category=template_item.category,
                item_name=template_item.item_name,
                quantity=template_item.quantity,
                notes=template_item.notes,
                order=template_item.order,
            )

        logger.info(
            "packing_list_created_from_template",
            template_id=str(self.id),
            template_name=self.name,
            packing_list_id=str(packing_list.id),
            trip_id=str(trip.id),
            item_count=self.items.count(),
        )

        return packing_list


class PackingListTemplateItem(models.Model):
    """
    Individual item in a packing list template.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        PackingListTemplate,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("template"),
    )
    category = models.CharField(
        _("category"), max_length=100, help_text=_("e.g., Clothing, Electronics, Toiletries")
    )
    item_name = models.CharField(_("item name"), max_length=200)
    quantity = models.PositiveIntegerField(
        _("quantity"), default=1, validators=[MinValueValidator(1)]
    )
    notes = models.TextField(_("notes"), blank=True)
    order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("template item")
        verbose_name_plural = _("template items")
        db_table = "packing_list_template_items"
        ordering = ["category", "order", "item_name"]
        indexes = [
            models.Index(fields=["template", "category"]),
        ]

    def __str__(self):
        return f"{self.item_name} ({self.quantity})"


class TripPackingList(models.Model):
    """
    Packing list instance for a specific trip.
    Can be assigned to a specific person or be a general list.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="packing_lists", verbose_name=_("trip")
    )
    name = models.CharField(
        _("list name"),
        max_length=200,
        help_text=_("e.g., 'David's List', 'Kids' List', 'Beach Gear'"),
    )
    based_on_template = models.ForeignKey(
        PackingListTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trip_lists",
        verbose_name=_("based on template"),
        help_text=_("Template this list was created from (if any)"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_packing_lists",
        verbose_name=_("assigned to"),
        help_text=_("Person responsible for this list"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("trip packing list")
        verbose_name_plural = _("trip packing lists")
        db_table = "trip_packing_lists"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["trip"]),
            models.Index(fields=["assigned_to"]),
        ]

    def __str__(self):
        if self.assigned_to:
            return f"{self.name} - {self.trip.name} ({self.assigned_to.get_full_name() or self.assigned_to.username})"
        return f"{self.name} - {self.trip.name}"

    def get_absolute_url(self):
        """Return the URL for this packing list's detail page."""
        return reverse("packing:list_detail", kwargs={"pk": self.pk})

    def get_packed_percentage(self):
        """Calculate percentage of items packed."""
        total_items = self.items.count()
        if total_items == 0:
            return 0
        packed_items = self.items.filter(is_packed=True).count()
        return int((packed_items / total_items) * 100)

    def get_packed_count(self):
        """Return count of packed items."""
        return self.items.filter(is_packed=True).count()

    def get_total_count(self):
        """Return total count of items."""
        return self.items.count()

    def save_as_template(self, template_name, description=""):
        """
        Save this packing list as a new reusable template.

        Args:
            template_name: Name for the new template
            description: Optional description

        Returns:
            PackingListTemplate instance
        """
        # Create the template
        template = PackingListTemplate.objects.create(
            name=template_name,
            description=description,
            is_system_template=False,
            created_by=self.assigned_to or self.trip.created_by,
        )

        # Copy all items
        for item in self.items.all():
            PackingListTemplateItem.objects.create(
                template=template,
                category=item.category,
                item_name=item.item_name,
                quantity=item.quantity,
                notes=item.notes,
                order=item.order,
            )

        logger.info(
            "packing_template_created_from_list",
            packing_list_id=str(self.id),
            template_id=str(template.id),
            template_name=template_name,
            item_count=self.items.count(),
        )

        return template


class TripPackingItem(models.Model):
    """
    Individual item in a trip-specific packing list.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    packing_list = models.ForeignKey(
        TripPackingList,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("packing list"),
    )
    category = models.CharField(
        _("category"), max_length=100, help_text=_("e.g., Clothing, Electronics, Toiletries")
    )
    item_name = models.CharField(_("item name"), max_length=200)
    quantity = models.PositiveIntegerField(
        _("quantity"), default=1, validators=[MinValueValidator(1)]
    )
    is_packed = models.BooleanField(_("packed"), default=False)
    notes = models.TextField(_("notes"), blank=True)
    order = models.PositiveIntegerField(_("display order"), default=0)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("packing item")
        verbose_name_plural = _("packing items")
        db_table = "trip_packing_items"
        ordering = ["category", "order", "item_name"]
        indexes = [
            models.Index(fields=["packing_list", "category"]),
            models.Index(fields=["packing_list", "is_packed"]),
        ]

    def __str__(self):
        packed_status = "✓" if self.is_packed else "☐"
        return f"{packed_status} {self.item_name} ({self.quantity})"
