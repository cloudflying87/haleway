from django.contrib import admin

from .models import (
    GroceryListTemplate,
    GroceryListTemplateItem,
    TripGroceryItem,
    TripGroceryList,
)


class GroceryListTemplateItemInline(admin.TabularInline):
    model = GroceryListTemplateItem
    extra = 1
    fields = ["category", "item_name", "quantity", "notes", "order"]


@admin.register(GroceryListTemplate)
class GroceryListTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "is_system_template", "created_by", "created_at"]
    list_filter = ["is_system_template", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [GroceryListTemplateItemInline]

    fieldsets = (
        (
            "Template Information",
            {"fields": ("name", "description", "family", "is_system_template", "created_by")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(GroceryListTemplateItem)
class GroceryListTemplateItemAdmin(admin.ModelAdmin):
    list_display = ["item_name", "quantity", "category", "template", "order"]
    list_filter = ["category", "template"]
    search_fields = ["item_name", "notes"]
    list_editable = ["order"]


class TripGroceryItemInline(admin.TabularInline):
    model = TripGroceryItem
    extra = 1
    fields = ["category", "item_name", "quantity", "is_purchased", "notes", "order"]


@admin.register(TripGroceryList)
class TripGroceryListAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "trip",
        "assigned_to",
        "shopping_date",
        "store_name",
        "purchased_count",
        "total_count",
        "percentage",
    ]
    list_filter = ["shopping_date", "trip", "assigned_to"]
    search_fields = ["name", "trip__name", "store_name"]
    readonly_fields = ["created_at", "updated_at", "based_on_template"]
    inlines = [TripGroceryItemInline]

    fieldsets = (
        ("List Information", {"fields": ("trip", "name", "based_on_template")}),
        ("Shopping Details", {"fields": ("assigned_to", "shopping_date", "store_name")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Purchased")
    def purchased_count(self, obj):
        return obj.get_purchased_count()

    @admin.display(description="Total")
    def total_count(self, obj):
        return obj.get_total_count()

    @admin.display(description="Progress")
    def percentage(self, obj):
        return f"{obj.get_purchased_percentage()}%"


@admin.register(TripGroceryItem)
class TripGroceryItemAdmin(admin.ModelAdmin):
    list_display = ["item_name", "quantity", "category", "grocery_list", "is_purchased", "order"]
    list_filter = ["category", "is_purchased", "grocery_list__trip"]
    search_fields = ["item_name", "notes"]
    list_editable = ["is_purchased", "order"]
