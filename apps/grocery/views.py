import structlog
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.trips.models import Trip

from .forms import (
    BulkGroceryItemForm,
    GroceryListTemplateForm,
    SaveAsTemplateForm,
    TripGroceryItemForm,
    TripGroceryListForm,
)
from .models import (
    GroceryListTemplate,
    TripGroceryItem,
    TripGroceryList,
)

logger = structlog.get_logger(__name__)


# ============================================================================
# TEMPLATE VIEWS
# ============================================================================


@login_required
def template_list(request):
    """List all grocery templates (system + family)"""
    # Get user's families
    user_families = request.user.family_memberships.values_list("family_id", flat=True)

    # System templates + family templates
    templates = (
        GroceryListTemplate.objects.filter(
            Q(is_system_template=True) | Q(family_id__in=user_families)
        )
        .annotate(item_count=Count("items"))
        .order_by("is_system_template", "name")
    )

    # Check if we're selecting for a specific trip
    trip_pk = request.GET.get("trip")
    trip = None
    if trip_pk:
        trip = get_object_or_404(Trip, pk=trip_pk)
        # Verify user has access to this trip
        if trip.family_id not in user_families:
            messages.error(request, "You don't have permission to view this trip.")
            return redirect("trips:trip_list")

    context = {
        "templates": templates,
        "trip": trip,
    }
    return render(request, "grocery/template_list.html", context)


@login_required
def template_detail(request, pk):
    """View grocery template details"""
    template = get_object_or_404(GroceryListTemplate, pk=pk)

    # Check permissions
    if not template.is_system_template:
        user_families = request.user.family_memberships.values_list("family_id", flat=True)
        if template.family_id not in user_families:
            messages.error(request, "You don't have permission to view this template.")
            return redirect("grocery:template_list")

    # Group items by category
    items = template.items.all()
    items_by_category = {}
    for item in items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    context = {
        "template": template,
        "items_by_category": items_by_category,
    }
    return render(request, "grocery/template_detail.html", context)


@login_required
def template_create(request):
    """Create a new grocery template"""
    if request.method == "POST":
        form = GroceryListTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            # Assign to user's first family (or could let them choose)
            first_family = request.user.family_memberships.first()
            if not first_family:
                messages.error(request, "You must be part of a family to create templates.")
                return redirect("grocery:template_list")

            template.family = first_family.family
            template.created_by = request.user
            template.is_system_template = False
            template.save()

            logger.info(
                "grocery_template_created",
                template_id=str(template.id),
                template_name=template.name,
                user_id=str(request.user.id),
            )

            messages.success(request, f'Template "{template.name}" created successfully!')
            return redirect("grocery:template_detail", pk=template.pk)
    else:
        form = GroceryListTemplateForm()

    context = {"form": form}
    return render(request, "grocery/template_form.html", context)


@login_required
def template_edit(request, pk):
    """Edit grocery template"""
    template = get_object_or_404(GroceryListTemplate, pk=pk)

    # Check permissions (can't edit system templates, must be in family)
    if template.is_system_template:
        messages.error(request, "System templates cannot be edited.")
        return redirect("grocery:template_detail", pk=pk)

    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if template.family_id not in user_families:
        messages.error(request, "You don't have permission to edit this template.")
        return redirect("grocery:template_list")

    if request.method == "POST":
        form = GroceryListTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully!')
            return redirect("grocery:template_detail", pk=template.pk)
    else:
        form = GroceryListTemplateForm(instance=template)

    context = {
        "form": form,
        "template": template,
    }
    return render(request, "grocery/template_form.html", context)


@login_required
def template_delete(request, pk):
    """Delete grocery template"""
    template = get_object_or_404(GroceryListTemplate, pk=pk)

    # Check permissions
    if template.is_system_template:
        messages.error(request, "System templates cannot be deleted.")
        return redirect("grocery:template_detail", pk=pk)

    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if template.family_id not in user_families:
        messages.error(request, "You don't have permission to delete this template.")
        return redirect("grocery:template_list")

    if request.method == "POST":
        template_name = template.name
        template.delete()

        logger.info(
            "grocery_template_deleted", template_name=template_name, user_id=str(request.user.id)
        )

        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect("grocery:template_list")

    context = {"template": template}
    return render(request, "grocery/template_confirm_delete.html", context)


# ============================================================================
# TRIP GROCERY LIST VIEWS
# ============================================================================


@login_required
def trip_grocery_lists(request, trip_pk):
    """List all grocery lists for a trip"""
    trip = get_object_or_404(Trip, pk=trip_pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if trip.family_id not in user_families:
        messages.error(request, "You don't have permission to view this trip.")
        return redirect("trips:trip_list")

    grocery_lists = trip.grocery_lists.annotate(
        item_count=Count("items"),
        purchased_count=Count("items", filter=Q(items__is_purchased=True)),
    ).order_by("shopping_date", "name")

    # Calculate percentage for each list
    for glist in grocery_lists:
        if glist.item_count > 0:
            glist.percentage = int((glist.purchased_count / glist.item_count) * 100)
        else:
            glist.percentage = 0

    context = {
        "trip": trip,
        "grocery_lists": grocery_lists,
    }
    return render(request, "grocery/trip_grocery_lists.html", context)


@login_required
def list_detail(request, pk):
    """View grocery list with checkbox UI"""
    grocery_list = get_object_or_404(TripGroceryList, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to view this list.")
        return redirect("trips:trip_list")

    # Group items by category
    items = grocery_list.items.all()
    items_by_category = {}
    for item in items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    # Calculate stats
    purchased_count = grocery_list.get_purchased_count()
    total_count = grocery_list.get_total_count()
    purchased_percentage = grocery_list.get_purchased_percentage()

    # Check if user can edit
    can_edit = True  # All family members can edit

    context = {
        "grocery_list": grocery_list,
        "items_by_category": items_by_category,
        "purchased_count": purchased_count,
        "total_count": total_count,
        "purchased_percentage": purchased_percentage,
        "can_edit": can_edit,
    }
    return render(request, "grocery/list_detail.html", context)


@login_required
def list_create_from_template(request, trip_pk, template_pk):
    """Create a trip grocery list from a template"""
    trip = get_object_or_404(Trip, pk=trip_pk)
    template = get_object_or_404(GroceryListTemplate, pk=template_pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if trip.family_id not in user_families:
        messages.error(request, "You don't have permission to create lists for this trip.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = TripGroceryListForm(request.POST, trip=trip)
        if form.is_valid():
            # Create list from template
            grocery_list = template.duplicate_for_trip(
                trip=trip,
                assigned_to=form.cleaned_data.get("assigned_to"),
                list_name=form.cleaned_data["name"],
            )

            # Update optional fields
            if form.cleaned_data.get("shopping_date"):
                grocery_list.shopping_date = form.cleaned_data["shopping_date"]
            if form.cleaned_data.get("store_name"):
                grocery_list.store_name = form.cleaned_data["store_name"]
            grocery_list.save()

            messages.success(request, f'Grocery list "{grocery_list.name}" created from template!')
            return redirect("grocery:list_detail", pk=grocery_list.pk)
    else:
        form = TripGroceryListForm(initial={"name": template.name}, trip=trip)

    context = {
        "form": form,
        "trip": trip,
        "template": template,
    }
    return render(request, "grocery/list_create_from_template.html", context)


@login_required
def list_create_blank(request, trip_pk):
    """Create a blank trip grocery list"""
    trip = get_object_or_404(Trip, pk=trip_pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if trip.family_id not in user_families:
        messages.error(request, "You don't have permission to create lists for this trip.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = TripGroceryListForm(request.POST, trip=trip)
        if form.is_valid():
            grocery_list = form.save(commit=False)
            grocery_list.trip = trip
            grocery_list.save()

            logger.info(
                "grocery_list_created",
                list_id=str(grocery_list.id),
                trip_id=str(trip.id),
                user_id=str(request.user.id),
            )

            messages.success(request, f'Grocery list "{grocery_list.name}" created!')
            return redirect("grocery:list_detail", pk=grocery_list.pk)
    else:
        form = TripGroceryListForm(trip=trip)

    context = {
        "form": form,
        "trip": trip,
    }
    return render(request, "grocery/list_create_blank.html", context)


@login_required
def list_edit(request, pk):
    """Edit grocery list"""
    grocery_list = get_object_or_404(TripGroceryList, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to edit this list.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = TripGroceryListForm(request.POST, instance=grocery_list, trip=grocery_list.trip)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grocery list "{grocery_list.name}" updated!')
            return redirect("grocery:list_detail", pk=grocery_list.pk)
    else:
        form = TripGroceryListForm(instance=grocery_list, trip=grocery_list.trip)

    context = {
        "form": form,
        "grocery_list": grocery_list,
    }
    return render(request, "grocery/list_form.html", context)


@login_required
def list_delete(request, pk):
    """Delete grocery list"""
    grocery_list = get_object_or_404(TripGroceryList, pk=pk)

    # Check permissions (only admins can delete)
    user_families = request.user.family_memberships.select_related("family").all()
    is_admin = any(
        member.family_id == grocery_list.trip.family_id and member.role in ["owner", "admin"]
        for member in user_families
    )

    if not is_admin:
        messages.error(request, "Only family admins can delete grocery lists.")
        return redirect("grocery:list_detail", pk=pk)

    if request.method == "POST":
        trip = grocery_list.trip
        list_name = grocery_list.name
        grocery_list.delete()

        logger.info(
            "grocery_list_deleted",
            list_name=list_name,
            trip_id=str(trip.id),
            user_id=str(request.user.id),
        )

        messages.success(request, f'Grocery list "{list_name}" deleted!')
        return redirect("grocery:trip_grocery_lists", trip_pk=trip.pk)

    context = {"grocery_list": grocery_list}
    return render(request, "grocery/list_confirm_delete.html", context)


# ============================================================================
# ITEM VIEWS
# ============================================================================


@login_required
def add_item(request, list_pk):
    """Add a single item to grocery list"""
    grocery_list = get_object_or_404(TripGroceryList, pk=list_pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to add items.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = TripGroceryItemForm(request.POST, grocery_list=grocery_list)
        if form.is_valid():
            item = form.save(commit=False)
            item.grocery_list = grocery_list
            item.save()
            messages.success(request, f'Item "{item.item_name}" added!')
            return redirect("grocery:list_detail", pk=grocery_list.pk)
    else:
        # Pre-fill category from query parameter if provided
        category = request.GET.get("category", "")
        initial_data = {"category": category} if category else {}
        form = TripGroceryItemForm(initial=initial_data, grocery_list=grocery_list)

    context = {
        "form": form,
        "grocery_list": grocery_list,
    }
    return render(request, "grocery/item_form.html", context)


@login_required
def bulk_add_items(request, list_pk):
    """Bulk add items to grocery list"""
    grocery_list = get_object_or_404(TripGroceryList, pk=list_pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to add items.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = BulkGroceryItemForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data.get("category") or "Groceries"
            items_created = 0

            for item_data in form.parsed_items:
                TripGroceryItem.objects.create(
                    grocery_list=grocery_list,
                    category=category,
                    item_name=item_data["item_name"],
                    quantity=item_data["quantity"],
                    is_purchased=False,
                )
                items_created += 1

            logger.info(
                "grocery_items_bulk_added",
                list_id=str(grocery_list.id),
                items_created=items_created,
                category=category,
                user_id=str(request.user.id),
            )

            messages.success(request, f'{items_created} items added to "{grocery_list.name}"!')
            return redirect("grocery:list_detail", pk=grocery_list.pk)
    else:
        form = BulkGroceryItemForm()

    context = {
        "form": form,
        "grocery_list": grocery_list,
    }
    return render(request, "grocery/bulk_add_items.html", context)


@login_required
def edit_item(request, pk):
    """Edit grocery item"""
    item = get_object_or_404(TripGroceryItem, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if item.grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to edit this item.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = TripGroceryItemForm(request.POST, instance=item, grocery_list=item.grocery_list)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated!")
            return redirect("grocery:list_detail", pk=item.grocery_list.pk)
    else:
        form = TripGroceryItemForm(instance=item, grocery_list=item.grocery_list)

    context = {
        "form": form,
        "item": item,
    }
    return render(request, "grocery/item_form.html", context)


@login_required
def delete_item(request, pk):
    """Delete grocery item"""
    item = get_object_or_404(TripGroceryItem, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if item.grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to delete this item.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        grocery_list = item.grocery_list
        item_name = item.item_name
        item.delete()
        messages.success(request, f'Item "{item_name}" deleted!')
        return redirect("grocery:list_detail", pk=grocery_list.pk)

    context = {"item": item}
    return render(request, "grocery/item_confirm_delete.html", context)


@require_POST
@login_required
def toggle_purchased(request, pk):
    """Toggle item purchased status (AJAX)"""
    item = get_object_or_404(TripGroceryItem, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if item.grocery_list.trip.family_id not in user_families:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    # Toggle purchased status
    item.is_purchased = not item.is_purchased
    item.save()

    # Get updated stats
    grocery_list = item.grocery_list
    purchased_count = grocery_list.get_purchased_count()
    total_count = grocery_list.get_total_count()
    percentage = grocery_list.get_purchased_percentage()

    logger.info(
        "grocery_item_toggled",
        item_id=str(item.id),
        is_purchased=item.is_purchased,
        user_id=str(request.user.id),
    )

    return JsonResponse(
        {
            "success": True,
            "is_purchased": item.is_purchased,
            "purchased_count": purchased_count,
            "total_count": total_count,
            "percentage": percentage,
        }
    )


@login_required
def save_as_template(request, pk):
    """Save grocery list as a template"""
    grocery_list = get_object_or_404(TripGroceryList, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to save this as a template.")
        return redirect("trips:trip_list")

    if request.method == "POST":
        form = SaveAsTemplateForm(request.POST)
        if form.is_valid():
            template = grocery_list.save_as_template(
                name=form.cleaned_data["name"],
                description=form.cleaned_data.get("description", ""),
                family=grocery_list.trip.family,
                created_by=request.user,
            )

            messages.success(request, f'Template "{template.name}" created from this list!')
            return redirect("grocery:template_detail", pk=template.pk)
    else:
        form = SaveAsTemplateForm(initial={"name": f"{grocery_list.name} Template"})

    context = {
        "form": form,
        "grocery_list": grocery_list,
    }
    return render(request, "grocery/save_as_template.html", context)


@login_required
def list_print(request, pk):
    """Print-friendly grocery list view"""
    grocery_list = get_object_or_404(TripGroceryList, pk=pk)

    # Check permissions
    user_families = request.user.family_memberships.values_list("family_id", flat=True)
    if grocery_list.trip.family_id not in user_families:
        messages.error(request, "You don't have permission to view this list.")
        return redirect("trips:trip_list")

    # Group items by category
    items = grocery_list.items.all()
    items_by_category = {}
    for item in items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    context = {
        "grocery_list": grocery_list,
        "items_by_category": items_by_category,
    }
    return render(request, "grocery/list_print.html", context)
