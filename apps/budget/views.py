"""
Views for budget management.
"""

from decimal import Decimal

import structlog
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .forms import BudgetCategoryForm, BudgetCSVImportForm, BudgetItemForm
from .models import BudgetCategory, BudgetItem

logger = structlog.get_logger(__name__)
User = get_user_model()


class TripBudgetView(LoginRequiredMixin, ListView):
    """Display budget overview for a trip with categories and items."""

    model = BudgetItem
    template_name = "budget/budget_overview.html"
    context_object_name = "budget_items"

    def get_queryset(self):
        """Return budget items for the specified trip."""
        self.trip = get_object_or_404(
            Trip, pk=self.kwargs["trip_pk"], family__members__user=self.request.user
        )

        queryset = BudgetItem.objects.filter(trip=self.trip).select_related(
            "category", "paid_by", "created_by"
        )

        # Handle filtering by category
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Handle filtering by payment status
        paid_filter = self.request.GET.get("paid")
        if paid_filter == "yes":
            queryset = queryset.filter(actual_amount__isnull=False)
        elif paid_filter == "no":
            queryset = queryset.filter(actual_amount__isnull=True)

        return queryset.order_by("category__order", "category__name", "-created_at")

    def get_context_data(self, **kwargs):
        """Add trip, categories, and totals context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["categories"] = BudgetCategory.objects.filter(trip=self.trip).order_by(
            "order", "name"
        )

        # Calculate totals
        all_items = BudgetItem.objects.filter(trip=self.trip)
        context["total_estimated"] = all_items.aggregate(total=Sum("estimated_amount"))[
            "total"
        ] or Decimal("0.00")
        context["total_actual"] = all_items.aggregate(total=Sum("actual_amount"))[
            "total"
        ] or Decimal("0.00")
        context["total_variance"] = context["total_estimated"] - context["total_actual"]

        # Get family members for paid_by dropdown
        context["family_members"] = User.objects.filter(
            family_memberships__family=self.trip.family
        ).distinct()

        # Check permissions
        try:
            membership = FamilyMember.objects.get(family=self.trip.family, user=self.request.user)
            context["can_create"] = True  # All members can create
            context["can_edit"] = True  # All members can edit
            context["can_delete"] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context["can_create"] = False
            context["can_edit"] = False
            context["can_delete"] = False

        return context


class BudgetCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget category."""

    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = "budget/category_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.trip = get_object_or_404(
            Trip, pk=self.kwargs["trip_pk"], family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["page_title"] = f"Add Budget Category to {self.trip.name}"
        return context

    def form_valid(self, form):
        """Save the category."""
        category = form.save()

        logger.info(
            "budget_category_created",
            category_id=str(category.id),
            category_name=category.name,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id,
        )

        messages.success(
            self.request, _('Budget category "{}" added successfully!').format(category.name)
        )

        return redirect("budget:budget_overview", trip_pk=self.trip.pk)


class BudgetCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update budget category details."""

    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = "budget/category_form.html"

    def get_queryset(self):
        """Ensure user can only edit categories they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return BudgetCategory.objects.filter(trip__family__in=user_families)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.object.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.object.trip
        context["page_title"] = f"Edit {self.object.name}"
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "budget_category_updated",
            category_id=str(self.object.id),
            category_name=self.object.name,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Budget category updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy("budget:budget_overview", kwargs={"trip_pk": self.object.trip.pk})


class BudgetCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a budget category."""

    model = BudgetCategory
    template_name = "budget/category_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete categories."""
        admin_families = Family.objects.filter(
            members__user=self.request.user, members__role__in=["owner", "admin"]
        )
        return BudgetCategory.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy("budget:budget_overview", kwargs={"trip_pk": self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        category = self.get_object()
        logger.info(
            "budget_category_deleted",
            category_id=str(category.id),
            category_name=category.name,
            user_id=request.user.id,
        )
        messages.success(request, _("Budget category deleted successfully."))
        return super().delete(request, *args, **kwargs)


class BudgetItemCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget item."""

    model = BudgetItem
    form_class = BudgetItemForm
    template_name = "budget/item_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.trip = get_object_or_404(
            Trip, pk=self.kwargs["trip_pk"], family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip, creator, and family members to form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.trip
        kwargs["created_by"] = self.request.user
        kwargs["family_members"] = User.objects.filter(
            family_memberships__family=self.trip.family
        ).distinct()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["page_title"] = f"Add Budget Item to {self.trip.name}"
        return context

    def form_valid(self, form):
        """Save the budget item."""
        item = form.save()

        logger.info(
            "budget_item_created",
            item_id=str(item.id),
            description=item.description,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id,
        )

        messages.success(
            self.request, _('Budget item "{}" added successfully!').format(item.description)
        )

        return redirect("budget:budget_overview", trip_pk=self.trip.pk)


class BudgetItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update budget item details."""

    model = BudgetItem
    form_class = BudgetItemForm
    template_name = "budget/item_form.html"

    def get_queryset(self):
        """Ensure user can only edit items they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return BudgetItem.objects.filter(trip__family__in=user_families)

    def get_form_kwargs(self):
        """Pass trip, creator, and family members to form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.object.trip
        kwargs["created_by"] = self.request.user
        kwargs["family_members"] = User.objects.filter(
            family_memberships__family=self.object.trip.family
        ).distinct()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.object.trip
        context["page_title"] = f"Edit {self.object.description}"
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "budget_item_updated",
            item_id=str(self.object.id),
            description=self.object.description,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Budget item updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy("budget:budget_overview", kwargs={"trip_pk": self.object.trip.pk})


class BudgetItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a budget item."""

    model = BudgetItem
    template_name = "budget/item_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete items."""
        admin_families = Family.objects.filter(
            members__user=self.request.user, members__role__in=["owner", "admin"]
        )
        return BudgetItem.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy("budget:budget_overview", kwargs={"trip_pk": self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        item = self.get_object()
        logger.info(
            "budget_item_deleted",
            item_id=str(item.id),
            description=item.description,
            user_id=request.user.id,
        )
        messages.success(request, _("Budget item deleted successfully."))
        return super().delete(request, *args, **kwargs)


@login_required
def add_activity_to_budget(request, activity_pk):
    """
    Create a budget item from an activity's estimated cost.
    """
    from apps.activities.models import Activity

    # Get the activity and verify user has access
    activity = get_object_or_404(Activity, pk=activity_pk, trip__family__members__user=request.user)

    trip = activity.trip

    # Check if user can edit
    try:
        FamilyMember.objects.get(family=trip.family, user=request.user)
    except FamilyMember.DoesNotExist:
        messages.error(request, _("You do not have permission to add budget items."))
        return redirect("activities:activity_detail", pk=activity_pk)

    # Check if activity has a cost
    if not activity.estimated_cost:
        messages.warning(request, _("This activity does not have an estimated cost."))
        return redirect("activities:activity_detail", pk=activity_pk)

    # Get or create "Activities" category
    category, created = BudgetCategory.objects.get_or_create(
        trip=trip,
        name="Activities",
        defaults={
            "color_code": "#06A77D",  # Palm Green
            "order": 2,  # After lodging (0) and food (1)
        },
    )

    # Check if this activity already has a budget item
    existing_item = BudgetItem.objects.filter(
        trip=trip, description=activity.name, estimated_amount=activity.estimated_cost
    ).first()

    if existing_item:
        messages.info(
            request,
            _('This activity is already in the budget as "{}".').format(existing_item.description),
        )
        return redirect("activities:activity_detail", pk=activity_pk)

    # Create the budget item
    budget_item = BudgetItem.objects.create(
        trip=trip,
        category=category,
        description=activity.name,
        estimated_amount=activity.estimated_cost,
        notes=f"Added from activity: {activity.name}",
        created_by=request.user,
    )

    logger.info(
        "budget_item_created_from_activity",
        item_id=str(budget_item.id),
        activity_id=str(activity.id),
        trip_id=str(trip.id),
        user_id=request.user.id,
        amount=float(activity.estimated_cost),
    )

    messages.success(
        request, _('Added "{}" to budget (${})').format(activity.name, activity.estimated_cost)
    )

    return redirect("activities:activity_detail", pk=activity_pk)


@login_required
@require_POST
def add_item_ajax(request, trip_pk):
    """
    AJAX endpoint to add a budget item from modal form.
    Returns JSON response with success/error status.
    """
    trip = get_object_or_404(Trip, pk=trip_pk, family__members__user=request.user)

    # Check permissions
    try:
        FamilyMember.objects.get(family=trip.family, user=request.user)
    except FamilyMember.DoesNotExist:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    # Get family members for paid_by dropdown
    family_members = User.objects.filter(family_memberships__family=trip.family).distinct()

    form = BudgetItemForm(
        request.POST, trip=trip, created_by=request.user, family_members=family_members
    )

    if form.is_valid():
        item = form.save()

        logger.info(
            "budget_item_created_ajax",
            item_id=str(item.id),
            description=item.description,
            trip_id=str(trip.id),
            user_id=request.user.id,
        )

        return JsonResponse(
            {
                "success": True,
                "item": {
                    "id": str(item.id),
                    "description": item.description,
                    "estimated_amount": float(item.estimated_amount),
                    "category": item.category.name if item.category else None,
                },
                "message": f'Budget item "{item.description}" added successfully!',
            }
        )
    else:
        # Return form errors
        errors = {field: errors[0] for field, errors in form.errors.items()}
        return JsonResponse({"success": False, "errors": errors}, status=400)


@login_required
def import_csv(request, trip_pk):
    """
    Import budget items from CSV file.
    """
    trip = get_object_or_404(Trip, pk=trip_pk, family__members__user=request.user)

    # Check permissions
    try:
        FamilyMember.objects.get(family=trip.family, user=request.user)
    except FamilyMember.DoesNotExist:
        messages.error(request, _("You do not have permission to import budget items."))
        return redirect("budget:budget_overview", trip_pk=trip.pk)

    # Get family members for CSV parsing
    family_members = User.objects.filter(family_memberships__family=trip.family).distinct()

    if request.method == "POST":
        form = BudgetCSVImportForm(
            request.POST, request.FILES, trip=trip, family_members=family_members
        )

        if form.is_valid():
            try:
                items_data = form.parse_csv()

                # Create budget items in a transaction
                with transaction.atomic():
                    created_items = []
                    for item_data in items_data:
                        item = BudgetItem.objects.create(
                            trip=trip,
                            description=item_data["description"],
                            estimated_amount=item_data["estimated_amount"],
                            category=item_data.get("category"),
                            actual_amount=item_data.get("actual_amount"),
                            paid_by=item_data.get("paid_by"),
                            payment_date=item_data.get("payment_date"),
                            notes=item_data.get("notes", ""),
                            created_by=request.user,
                        )
                        created_items.append(item)

                logger.info(
                    "budget_items_imported_from_csv",
                    trip_id=str(trip.id),
                    user_id=request.user.id,
                    items_count=len(created_items),
                )

                messages.success(
                    request,
                    _(f"Successfully imported {len(created_items)} budget items from CSV!"),
                )
                return redirect("budget:budget_overview", trip_pk=trip.pk)

            except Exception as e:
                logger.error("budget_csv_import_failed", trip_id=str(trip.id), error=str(e))
                messages.error(request, _(f"Error importing CSV: {str(e)}"))

    else:
        form = BudgetCSVImportForm(trip=trip, family_members=family_members)

    return render(
        request,
        "budget/import_csv.html",
        {
            "form": form,
            "trip": trip,
        },
    )
