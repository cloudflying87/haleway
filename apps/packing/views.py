"""
Views for packing list management.
"""

import structlog
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .forms import (
    BulkPackingItemForm,
    OutfitCalculatorForm,
    PackingItemForm,
    PackingListTemplateForm,
)
from .models import PackingListTemplate, TripPackingItem, TripPackingList
from .weather import WeatherService

logger = structlog.get_logger(__name__)


# ============================================================================
# Template Management Views
# ============================================================================


class TemplateListView(LoginRequiredMixin, ListView):
    """List all packing list templates (system + user-created)."""

    model = PackingListTemplate
    template_name = "packing/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        """Return system templates and user's custom templates."""
        return (
            PackingListTemplate.objects.filter(
                Q(is_system_template=True) | Q(created_by=self.request.user)
            )
            .prefetch_related("items")
            .order_by("-is_system_template", "name")
        )

    def get_context_data(self, **kwargs):
        """Add template categories to context."""
        context = super().get_context_data(**kwargs)
        templates = context["templates"]
        context["system_templates"] = templates.filter(is_system_template=True)
        context["custom_templates"] = templates.filter(is_system_template=False)
        return context


class TemplateDetailView(LoginRequiredMixin, DetailView):
    """Display template details with all items."""

    model = PackingListTemplate
    template_name = "packing/template_detail.html"
    context_object_name = "template"

    def get_queryset(self):
        """Ensure user can only view system templates or their own."""
        return PackingListTemplate.objects.filter(
            Q(is_system_template=True) | Q(created_by=self.request.user)
        ).prefetch_related("items")

    def get_context_data(self, **kwargs):
        """Add items grouped by category."""
        context = super().get_context_data(**kwargs)
        template = self.object

        # Group items by category
        items_by_category = {}
        for item in template.items.all():
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)

        context["items_by_category"] = items_by_category
        context["can_edit"] = (
            not template.is_system_template and template.created_by == self.request.user
        )
        context["can_delete"] = (
            not template.is_system_template and template.created_by == self.request.user
        )

        return context


class TemplateCreateView(LoginRequiredMixin, CreateView):
    """Create a new custom packing list template."""

    model = PackingListTemplate
    form_class = PackingListTemplateForm
    template_name = "packing/template_form.html"

    def form_valid(self, form):
        """Set the creator and mark as custom template."""
        template = form.save(commit=False)
        template.created_by = self.request.user
        template.is_system_template = False
        template.save()

        logger.info(
            "packing_template_created",
            template_id=str(template.id),
            template_name=template.name,
            user_id=self.request.user.id,
        )

        messages.success(
            self.request, f'Template "{template.name}" created successfully! Now add items to it.'
        )
        return redirect("packing:template_detail", pk=template.pk)


class TemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a custom packing list template."""

    model = PackingListTemplate
    form_class = PackingListTemplateForm
    template_name = "packing/template_form.html"

    def get_queryset(self):
        """Only allow editing user's own custom templates."""
        return PackingListTemplate.objects.filter(
            created_by=self.request.user, is_system_template=False
        )

    def form_valid(self, form):
        """Save the template."""
        template = form.save()

        logger.info(
            "packing_template_updated",
            template_id=str(template.id),
            template_name=template.name,
            user_id=self.request.user.id,
        )

        messages.success(self.request, f'Template "{template.name}" updated successfully!')
        return redirect("packing:template_detail", pk=template.pk)


class TemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a custom packing list template."""

    model = PackingListTemplate
    template_name = "packing/template_confirm_delete.html"
    success_url = reverse_lazy("packing:template_list")

    def get_queryset(self):
        """Only allow deleting user's own custom templates."""
        return PackingListTemplate.objects.filter(
            created_by=self.request.user, is_system_template=False
        )

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        template = self.get_object()
        template_name = template.name

        logger.info(
            "packing_template_deleted",
            template_id=str(template.id),
            template_name=template_name,
            user_id=request.user.id,
        )

        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Trip Packing List Views
# ============================================================================


class PackingListDetailView(LoginRequiredMixin, DetailView):
    """Display packing list details with items and progress."""

    model = TripPackingList
    template_name = "packing/packing_list_detail.html"
    context_object_name = "packing_list"

    def get_queryset(self):
        """Ensure user can only view lists from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return (
            TripPackingList.objects.filter(trip__family__in=user_families)
            .select_related("trip", "based_on_template")
            .prefetch_related("items")
        )

    def get_context_data(self, **kwargs):
        """Add items grouped by category and permissions."""
        context = super().get_context_data(**kwargs)
        packing_list = self.object

        # Group items by category
        items_by_category = {}
        for item in packing_list.items.all():
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            items_by_category[item.category].append(item)

        context["items_by_category"] = items_by_category
        context["packed_percentage"] = packing_list.get_packed_percentage()
        context["packed_count"] = packing_list.get_packed_count()
        context["total_count"] = packing_list.get_total_count()

        # Get weather forecast if resort has coordinates
        trip = packing_list.trip
        if hasattr(trip, "resort") and trip.resort:
            resort = trip.resort
            if resort.latitude and resort.longitude:
                weather_forecast = WeatherService.get_forecast(
                    latitude=float(resort.latitude),
                    longitude=float(resort.longitude),
                    start_date=trip.start_date,
                    end_date=trip.end_date,
                )
                context["weather_forecast"] = weather_forecast
                if weather_forecast:
                    # Calculate temperature range for the trip
                    highs = [day["high"] for day in weather_forecast if day["high"] is not None]
                    lows = [day["low"] for day in weather_forecast if day["low"] is not None]
                    if highs and lows:
                        context["temp_range"] = {"high": max(highs), "low": min(lows)}

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=packing_list.trip.family, user=self.request.user
            )
            context["can_edit"] = True
            context["can_delete"] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context["can_edit"] = False
            context["can_delete"] = False

        return context


@login_required
def create_or_get_packing_list(request, trip_pk):
    """Get or create the packing list for a trip, optionally from a template."""
    trip = get_object_or_404(Trip, pk=trip_pk, family__members__user=request.user)

    # Check if list already exists
    try:
        packing_list = TripPackingList.objects.get(trip=trip)
        # List already exists, redirect to it
        return redirect("packing:list_detail", pk=packing_list.pk)
    except TripPackingList.DoesNotExist:
        pass

    if request.method == "POST":
        template_id = request.POST.get("template_id")

        # Check if starting from template or blank
        if template_id:
            # Get the template
            template = get_object_or_404(PackingListTemplate, pk=template_id)

            # Create the packing list from template
            packing_list = template.duplicate_for_trip(trip=trip)

            messages.success(
                request, f'Packing list created successfully from "{template.name}" template!'
            )
        else:
            # Create blank packing list
            packing_list = TripPackingList.objects.create(trip=trip)

            logger.info(
                "blank_packing_list_created",
                packing_list_id=str(packing_list.id),
                trip_id=str(trip.id),
                user_id=request.user.id,
            )

            messages.success(
                request,
                "Packing list created successfully! Add items using the buttons below.",
            )

        return redirect("packing:list_detail", pk=packing_list.pk)

    # GET request - show template selection form
    templates = PackingListTemplate.objects.filter(
        Q(is_system_template=True) | Q(created_by=request.user)
    ).order_by("-is_system_template", "name")

    return render(
        request,
        "packing/create_packing_list.html",
        {
            "trip": trip,
            "templates": templates,
        },
    )


@login_required
def save_as_template(request, pk):
    """Save a trip packing list as a new template."""
    packing_list = get_object_or_404(
        TripPackingList, pk=pk, trip__family__members__user=request.user
    )

    if request.method == "POST":
        template_name = request.POST.get("template_name")
        description = request.POST.get("description", "")

        # Create the template
        template = packing_list.save_as_template(
            template_name=template_name, description=description, created_by=request.user
        )

        messages.success(
            request,
            f'Template "{template.name}" created successfully! You can now use it for future trips.',
        )
        return redirect("packing:template_detail", pk=template.pk)

    return render(request, "packing/save_as_template.html", {"packing_list": packing_list})


@login_required
def print_packing_list(request, pk):
    """Print view for packing list - optimized for printing on one page."""
    packing_list = get_object_or_404(
        TripPackingList, pk=pk, trip__family__members__user=request.user
    )

    # Group items by category
    items_by_category = {}
    for item in packing_list.items.all():
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    return render(
        request,
        "packing/print_packing_list.html",
        {
            "packing_list": packing_list,
            "items_by_category": items_by_category,
            "packed_percentage": packing_list.get_packed_percentage(),
            "packed_count": packing_list.get_packed_count(),
            "total_count": packing_list.get_total_count(),
        },
    )


# ============================================================================
# Packing Item Management
# ============================================================================


@login_required
def add_packing_item(request, list_pk):
    """Add a new item to a packing list."""
    packing_list = get_object_or_404(
        TripPackingList, pk=list_pk, trip__family__members__user=request.user
    )

    if request.method == "POST":
        form = PackingItemForm(request.POST, packing_list=packing_list)
        if form.is_valid():
            item = form.save(commit=False)
            item.packing_list = packing_list
            item.save()

            logger.info(
                "packing_item_added",
                item_id=str(item.id),
                item_name=item.item_name,
                packing_list_id=str(packing_list.id),
                user_id=request.user.id,
            )

            messages.success(request, f'Item "{item.item_name}" added successfully!')
            return redirect("packing:list_detail", pk=packing_list.pk)
    else:
        # Check if category is pre-filled from query parameter
        category = request.GET.get("category")
        if category:
            form = PackingItemForm(packing_list=packing_list, initial={"category": category})
        else:
            form = PackingItemForm(packing_list=packing_list)

    return render(request, "packing/add_item.html", {"packing_list": packing_list, "form": form})


@login_required
def toggle_packed(request, pk):
    """Toggle the packed status of an item (AJAX)."""
    item = get_object_or_404(
        TripPackingItem, pk=pk, packing_list__trip__family__members__user=request.user
    )

    item.is_packed = not item.is_packed
    item.save()

    logger.info(
        "packing_item_toggled",
        item_id=str(item.id),
        item_name=item.item_name,
        is_packed=item.is_packed,
        user_id=request.user.id,
    )

    return JsonResponse(
        {
            "success": True,
            "is_packed": item.is_packed,
            "packed_count": item.packing_list.get_packed_count(),
            "total_count": item.packing_list.get_total_count(),
            "percentage": item.packing_list.get_packed_percentage(),
        }
    )


@login_required
def edit_packing_item(request, pk):
    """Edit a packing item."""
    item = get_object_or_404(
        TripPackingItem, pk=pk, packing_list__trip__family__members__user=request.user
    )

    if request.method == "POST":
        form = PackingItemForm(request.POST, instance=item, packing_list=item.packing_list)
        if form.is_valid():
            item = form.save()

            logger.info(
                "packing_item_updated",
                item_id=str(item.id),
                item_name=item.item_name,
                user_id=request.user.id,
            )

            messages.success(request, f'Item "{item.item_name}" updated successfully!')
            return redirect("packing:list_detail", pk=item.packing_list.pk)
    else:
        form = PackingItemForm(instance=item, packing_list=item.packing_list)

    return render(request, "packing/edit_item.html", {"item": item, "form": form})


@login_required
def delete_packing_item(request, pk):
    """Delete a packing item."""
    item = get_object_or_404(
        TripPackingItem, pk=pk, packing_list__trip__family__members__user=request.user
    )

    packing_list = item.packing_list
    item_name = item.item_name

    if request.method == "POST":
        item.delete()

        logger.info(
            "packing_item_deleted",
            item_id=str(pk),
            item_name=item_name,
            packing_list_id=str(packing_list.id),
            user_id=request.user.id,
        )

        messages.success(request, f'Item "{item_name}" deleted successfully!')
        return redirect("packing:list_detail", pk=packing_list.pk)

    return render(request, "packing/delete_item.html", {"item": item})


# ============================================================================
# Outfit Calculator
# ============================================================================


@login_required
def add_outfit(request, list_pk):
    """Add clothing items based on number of outfits."""
    packing_list = get_object_or_404(
        TripPackingList, pk=list_pk, trip__family__members__user=request.user
    )

    if request.method == "POST":
        form = OutfitCalculatorForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            num_outfits = form.cleaned_data["num_outfits"]

            # Define outfit items with their quantities
            # For example: 5 outfits = 5 shirts, 3 pants, 5 underwear, 5 socks
            outfit_items = [
                (category, "Shirts", num_outfits, ""),
                (category, "Pants", max(3, num_outfits // 2), "Mix and match"),
                (category, "Underwear", num_outfits, ""),
                (category, "Socks", num_outfits, ""),
                (category, "Pajamas", 2, ""),
            ]

            # Get current max order for items in this category
            max_order = TripPackingItem.objects.filter(
                packing_list=packing_list, category=category
            ).count()

            # Create the items
            for order, (category, item_name, qty, notes) in enumerate(
                outfit_items, start=max_order + 1
            ):
                TripPackingItem.objects.create(
                    packing_list=packing_list,
                    category=category,
                    item_name=item_name,
                    quantity=qty,
                    notes=notes,
                    order=order,
                )

            logger.info(
                "outfit_items_added",
                num_outfits=num_outfits,
                category=category,
                packing_list_id=str(packing_list.id),
                items_added=len(outfit_items),
                user_id=request.user.id,
            )

            messages.success(request, f"Added {num_outfits} outfits to '{category}' successfully!")
            return redirect("packing:list_detail", pk=packing_list.pk)
    else:
        form = OutfitCalculatorForm()

    # Get existing categories for suggestions
    existing_categories = (
        TripPackingItem.objects.filter(packing_list=packing_list)
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "packing/add_outfit.html",
        {"packing_list": packing_list, "form": form, "existing_categories": existing_categories},
    )


@login_required
def bulk_add_items(request, list_pk):
    """Add multiple items at once via comma-separated input."""
    packing_list = get_object_or_404(
        TripPackingList, pk=list_pk, trip__family__members__user=request.user
    )

    if request.method == "POST":
        form = BulkPackingItemForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            parsed_items = form.cleaned_data["items"]  # Already parsed by clean_items()

            # Get current max order for this category
            max_order = TripPackingItem.objects.filter(
                packing_list=packing_list, category=category
            ).count()

            # Create all items
            items_created = []
            for idx, item_data in enumerate(parsed_items, start=max_order + 1):
                item = TripPackingItem.objects.create(
                    packing_list=packing_list,
                    category=category,
                    item_name=item_data["name"],
                    quantity=item_data["quantity"],
                    order=idx,
                )
                items_created.append(item)

            logger.info(
                "bulk_items_added",
                packing_list_id=str(packing_list.id),
                category=category,
                items_count=len(items_created),
                user_id=request.user.id,
            )

            messages.success(
                request, f"Added {len(items_created)} items to {category} successfully!"
            )
            return redirect("packing:list_detail", pk=packing_list.pk)
    else:
        form = BulkPackingItemForm()

    # Get existing categories for suggestions
    existing_categories = (
        TripPackingItem.objects.filter(packing_list=packing_list)
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "packing/bulk_add_items.html",
        {"packing_list": packing_list, "form": form, "existing_categories": existing_categories},
    )


@login_required
def rename_category(request, list_pk):
    """Rename a category for all items in a packing list (AJAX)."""
    packing_list = get_object_or_404(
        TripPackingList, pk=list_pk, trip__family__members__user=request.user
    )

    if request.method == "POST":
        old_category = request.POST.get("old_category")
        new_category = request.POST.get("new_category")

        if not old_category or not new_category:
            return JsonResponse({"success": False, "error": "Missing category name"}, status=400)

        if old_category == new_category:
            return JsonResponse(
                {"success": False, "error": "New category name must be different"}, status=400
            )

        # Update all items with this category
        updated_count = TripPackingItem.objects.filter(
            packing_list=packing_list, category=old_category
        ).update(category=new_category)

        logger.info(
            "packing_category_renamed",
            packing_list_id=str(packing_list.id),
            old_category=old_category,
            new_category=new_category,
            items_updated=updated_count,
            user_id=request.user.id,
        )

        return JsonResponse({"success": True, "items_updated": updated_count})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
