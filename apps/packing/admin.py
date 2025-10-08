"""
Django admin configuration for packing app.
"""

from django.contrib import admin

from .models import PackingListTemplate, PackingListTemplateItem, TripPackingItem, TripPackingList


class PackingListTemplateItemInline(admin.TabularInline):
    """Inline admin for template items."""

    model = PackingListTemplateItem
    extra = 3
    fields = ["category", "item_name", "quantity", "notes", "order"]


@admin.register(PackingListTemplate)
class PackingListTemplateAdmin(admin.ModelAdmin):
    """Admin interface for PackingListTemplate model."""

    list_display = ["name", "is_system_template", "created_by", "item_count", "created_at"]
    list_filter = ["is_system_template", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Template Information", {"fields": ("name", "description", "is_system_template")}),
        (
            "Metadata",
            {"fields": ("id", "created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    inlines = [PackingListTemplateItemInline]
    ordering = ["name"]

    @admin.display(description="Items")
    def item_count(self, obj):
        """Return the number of items in this template."""
        return obj.items.count()


class TripPackingItemInline(admin.TabularInline):
    """Inline admin for trip packing items."""

    model = TripPackingItem
    extra = 3
    fields = ["category", "item_name", "quantity", "is_packed", "notes", "order"]


@admin.register(TripPackingList)
class TripPackingListAdmin(admin.ModelAdmin):
    """Admin interface for TripPackingList model."""

    list_display = [
        "name",
        "trip",
        "assigned_to",
        "based_on_template",
        "packed_status",
        "created_at",
    ]
    list_filter = ["created_at", "trip__status"]
    search_fields = [
        "name",
        "trip__name",
        "trip__destination_name",
        "assigned_to__username",
        "assigned_to__email",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "packed_status"]
    fieldsets = (
        ("List Information", {"fields": ("trip", "name", "assigned_to", "based_on_template")}),
        ("Status", {"fields": ("packed_status",)}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [TripPackingItemInline]
    autocomplete_fields = ["trip"]
    ordering = ["-created_at"]

    @admin.display(description="Packed")
    def packed_status(self, obj):
        """Return packing status as percentage."""
        return f"{obj.get_packed_count()}/{obj.get_total_count()} ({obj.get_packed_percentage()}%)"


@admin.register(TripPackingItem)
class TripPackingItemAdmin(admin.ModelAdmin):
    """Admin interface for TripPackingItem model."""

    list_display = ["item_name", "packing_list", "category", "quantity", "is_packed", "created_at"]
    list_filter = ["is_packed", "category", "created_at"]
    search_fields = ["item_name", "category", "packing_list__name", "packing_list__trip__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Item Information", {"fields": ("packing_list", "category", "item_name", "quantity")}),
        ("Status", {"fields": ("is_packed", "notes")}),
        (
            "Metadata",
            {"fields": ("id", "order", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    ordering = ["packing_list", "category", "order", "item_name"]
