import uuid

import structlog
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

logger = structlog.get_logger(__name__)
User = get_user_model()


class GroceryListTemplate(models.Model):
    """Reusable grocery list template (system or custom)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        "families.Family",
        on_delete=models.CASCADE,
        related_name="grocery_templates",
        null=True,
        blank=True,
        help_text="Family that owns this template (null for system templates)",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_system_template = models.BooleanField(
        default=False, help_text="System templates cannot be deleted"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_grocery_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["family", "is_system_template"]),
        ]

    def __str__(self):
        if self.is_system_template:
            return f"{self.name} (System)"
        return self.name

    def get_absolute_url(self):
        return reverse("grocery:template_detail", kwargs={"pk": self.pk})

    def duplicate_for_trip(self, trip, assigned_to=None, list_name=None):
        """Create a TripGroceryList from this template"""
        grocery_list = TripGroceryList.objects.create(
            trip=trip, name=list_name or self.name, based_on_template=self, assigned_to=assigned_to
        )

        # Copy all template items to trip items
        for template_item in self.items.all():
            TripGroceryItem.objects.create(
                grocery_list=grocery_list,
                category=template_item.category,
                item_name=template_item.item_name,
                quantity=template_item.quantity,
                notes=template_item.notes,
                order=template_item.order,
                is_purchased=False,
            )

        logger.info(
            "grocery_list_created_from_template",
            template_id=str(self.id),
            template_name=self.name,
            trip_id=str(trip.id),
            list_id=str(grocery_list.id),
            item_count=self.items.count(),
        )

        return grocery_list


class GroceryListTemplateItem(models.Model):
    """Item within a grocery list template"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        GroceryListTemplate, on_delete=models.CASCADE, related_name="items"
    )
    category = models.CharField(
        max_length=100, help_text="e.g., Produce, Dairy, Meat, Snacks, Beverages"
    )
    item_name = models.CharField(max_length=200)
    quantity = models.CharField(
        max_length=100, blank=True, help_text="e.g., '2 lbs', '1 gallon', '6 pack'"
    )
    notes = models.TextField(blank=True)
    order = models.IntegerField(default=0, help_text="For custom sorting within category")

    class Meta:
        ordering = ["category", "order", "item_name"]
        indexes = [
            models.Index(fields=["template", "category"]),
        ]

    def __str__(self):
        if self.quantity:
            return f"{self.quantity} {self.item_name}"
        return self.item_name


class TripGroceryList(models.Model):
    """Trip-specific grocery list"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey("trips.Trip", on_delete=models.CASCADE, related_name="grocery_lists")
    name = models.CharField(
        max_length=200, help_text="e.g., 'Week 1 Groceries', 'Pre-Trip Shopping'"
    )
    based_on_template = models.ForeignKey(
        GroceryListTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trip_lists",
        help_text="Template this list was created from",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_grocery_lists",
        help_text="Family member assigned to this shopping trip",
    )
    shopping_date = models.DateField(null=True, blank=True)
    store_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["shopping_date", "name"]
        indexes = [
            models.Index(fields=["trip"]),
            models.Index(fields=["assigned_to"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.trip.name}"

    def get_absolute_url(self):
        return reverse("grocery:list_detail", kwargs={"pk": self.pk})

    def get_purchased_percentage(self):
        """Calculate percentage of items purchased"""
        total = self.items.count()
        if total == 0:
            return 0
        purchased = self.items.filter(is_purchased=True).count()
        return round((purchased / total) * 100)

    def get_purchased_count(self):
        """Get count of purchased items"""
        return self.items.filter(is_purchased=True).count()

    def get_total_count(self):
        """Get total item count"""
        return self.items.count()

    def save_as_template(self, name, description="", family=None, created_by=None):
        """Save this grocery list as a reusable template"""
        template = GroceryListTemplate.objects.create(
            family=family,
            name=name,
            description=description,
            is_system_template=False,
            created_by=created_by,
        )

        # Copy all items to template
        for item in self.items.all():
            GroceryListTemplateItem.objects.create(
                template=template,
                category=item.category,
                item_name=item.item_name,
                quantity=item.quantity,
                notes=item.notes,
                order=item.order,
            )

        logger.info(
            "grocery_template_saved",
            template_id=str(template.id),
            template_name=name,
            list_id=str(self.id),
            trip_id=str(self.trip.id),
            item_count=self.items.count(),
        )

        return template


class TripGroceryItem(models.Model):
    """Individual grocery item in a trip list"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grocery_list = models.ForeignKey(
        TripGroceryList, on_delete=models.CASCADE, related_name="items"
    )
    category = models.CharField(max_length=100)
    item_name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_purchased = models.BooleanField(default=False)
    order = models.IntegerField(default=0, help_text="For custom sorting within category")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "order", "item_name"]
        indexes = [
            models.Index(fields=["grocery_list", "category"]),
            models.Index(fields=["grocery_list", "is_purchased"]),
        ]

    def __str__(self):
        if self.quantity:
            return f"{self.quantity} {self.item_name}"
        return self.item_name
