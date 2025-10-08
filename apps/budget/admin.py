"""
Django admin configuration for budget app.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import BudgetCategory, BudgetItem


class BudgetItemInline(admin.TabularInline):
    """Inline admin for budget items within a category."""

    model = BudgetItem
    extra = 0
    readonly_fields = ["created_at", "updated_at", "variance"]
    fields = [
        "description",
        "estimated_amount",
        "actual_amount",
        "paid_by",
        "payment_date",
        "variance",
    ]
    show_change_link = True

    @admin.display(description="Variance")
    def variance(self, obj):
        """Display variance if actual amount is set."""
        if obj.variance is not None:
            color = "green" if obj.variance >= 0 else "red"
            return format_html('<span style="color: {};">${:.2f}</span>', color, obj.variance)
        return "-"


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    """Admin interface for BudgetCategory model."""

    list_display = [
        "name",
        "trip",
        "color_badge",
        "order",
        "item_count",
        "total_estimated",
        "total_actual",
    ]
    list_filter = ["trip"]
    search_fields = ["name", "trip__name"]
    readonly_fields = ["id"]
    inlines = [BudgetItemInline]

    fieldsets = (
        ("Category Information", {"fields": ("trip", "name", "color_code", "order")}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )

    @admin.display(description="Color")
    def color_badge(self, obj):
        """Display a colored badge for the category."""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.color_code,
            obj.get_color_code_display(),
        )

    @admin.display(description="Items")
    def item_count(self, obj):
        """Display the number of items in this category."""
        return obj.items.count()

    @admin.display(description="Est. Total")
    def total_estimated(self, obj):
        """Display total estimated amount for this category."""
        return f"${obj.get_total_estimated():.2f}"

    @admin.display(description="Actual Total")
    def total_actual(self, obj):
        """Display total actual amount for this category."""
        return f"${obj.get_total_actual():.2f}"


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    """Admin interface for BudgetItem model."""

    list_display = [
        "description",
        "trip",
        "category",
        "estimated_amount",
        "actual_amount",
        "variance_display",
        "paid_by",
        "payment_date",
        "is_paid",
    ]
    list_filter = ["category", "paid_by", "payment_date", "created_at"]
    search_fields = ["description", "notes", "trip__name"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "variance_display",
        "variance_percentage_display",
    ]
    date_hierarchy = "payment_date"

    fieldsets = (
        ("Budget Item Information", {"fields": ("trip", "category", "description", "notes")}),
        (
            "Amounts",
            {
                "fields": (
                    "estimated_amount",
                    "actual_amount",
                    "variance_display",
                    "variance_percentage_display",
                )
            },
        ),
        ("Payment Details", {"fields": ("paid_by", "payment_date")}),
        ("Creator & Timestamps", {"fields": ("created_by", "created_at", "updated_at")}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )

    @admin.display(description="Variance")
    def variance_display(self, obj):
        """Display variance with color coding."""
        if obj.variance is not None:
            color = "green" if obj.variance >= 0 else "red"
            return format_html(
                '<span style="color: {}; font-weight: bold;">${:.2f}</span>', color, obj.variance
            )
        return "-"

    @admin.display(description="Variance %")
    def variance_percentage_display(self, obj):
        """Display variance percentage with color coding."""
        if obj.variance_percentage is not None:
            color = "green" if obj.variance_percentage >= 0 else "red"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                obj.variance_percentage,
            )
        return "-"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("trip", "category", "paid_by", "created_by")
