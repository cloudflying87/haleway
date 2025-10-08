"""
Views for budget management.
"""
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
import structlog

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip
from .models import BudgetCategory, BudgetItem
from .forms import BudgetCategoryForm, BudgetItemForm

logger = structlog.get_logger(__name__)
User = get_user_model()


class TripBudgetView(LoginRequiredMixin, ListView):
    """Display budget overview for a trip with categories and items."""
    model = BudgetItem
    template_name = 'budget/budget_overview.html'
    context_object_name = 'budget_items'

    def get_queryset(self):
        """Return budget items for the specified trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )

        queryset = BudgetItem.objects.filter(trip=self.trip).select_related(
            'category', 'paid_by', 'created_by'
        )

        # Handle filtering by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Handle filtering by payment status
        paid_filter = self.request.GET.get('paid')
        if paid_filter == 'yes':
            queryset = queryset.filter(actual_amount__isnull=False)
        elif paid_filter == 'no':
            queryset = queryset.filter(actual_amount__isnull=True)

        return queryset.order_by('category__order', 'category__name', '-created_at')

    def get_context_data(self, **kwargs):
        """Add trip, categories, and totals context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['categories'] = BudgetCategory.objects.filter(trip=self.trip).order_by('order', 'name')

        # Calculate totals
        all_items = BudgetItem.objects.filter(trip=self.trip)
        context['total_estimated'] = all_items.aggregate(
            total=Sum('estimated_amount')
        )['total'] or Decimal('0.00')
        context['total_actual'] = all_items.aggregate(
            total=Sum('actual_amount')
        )['total'] or Decimal('0.00')
        context['total_variance'] = context['total_estimated'] - context['total_actual']

        # Get family members for paid_by dropdown
        context['family_members'] = User.objects.filter(
            family_memberships__family=self.trip.family
        ).distinct()

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=self.trip.family,
                user=self.request.user
            )
            context['can_create'] = True  # All members can create
            context['can_edit'] = True  # All members can edit
            context['can_delete'] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context['can_create'] = False
            context['can_edit'] = False
            context['can_delete'] = False

        return context


class BudgetCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget category."""
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'budget/category_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'Add Budget Category to {self.trip.name}'
        return context

    def form_valid(self, form):
        """Save the category."""
        category = form.save()

        logger.info(
            "budget_category_created",
            category_id=str(category.id),
            category_name=category.name,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id
        )

        messages.success(
            self.request,
            _('Budget category "{}" added successfully!').format(category.name)
        )

        return redirect('budget:budget_overview', trip_pk=self.trip.pk)


class BudgetCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update budget category details."""
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'budget/category_form.html'

    def get_queryset(self):
        """Ensure user can only edit categories they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return BudgetCategory.objects.filter(trip__family__in=user_families)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.object.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit {self.object.name}'
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "budget_category_updated",
            category_id=str(self.object.id),
            category_name=self.object.name,
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Budget category updated successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy('budget:budget_overview', kwargs={
            'trip_pk': self.object.trip.pk
        })


class BudgetCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a budget category."""
    model = BudgetCategory
    template_name = 'budget/category_confirm_delete.html'

    def get_queryset(self):
        """Ensure only admins can delete categories."""
        admin_families = Family.objects.filter(
            members__user=self.request.user,
            members__role__in=['owner', 'admin']
        )
        return BudgetCategory.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy('budget:budget_overview', kwargs={
            'trip_pk': self.object.trip.pk
        })

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        category = self.get_object()
        logger.info(
            "budget_category_deleted",
            category_id=str(category.id),
            category_name=category.name,
            user_id=request.user.id
        )
        messages.success(request, _('Budget category deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class BudgetItemCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget item."""
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'budget/item_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip, creator, and family members to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.trip
        kwargs['created_by'] = self.request.user
        kwargs['family_members'] = User.objects.filter(
            family_memberships__family=self.trip.family
        ).distinct()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'Add Budget Item to {self.trip.name}'
        return context

    def form_valid(self, form):
        """Save the budget item."""
        item = form.save()

        logger.info(
            "budget_item_created",
            item_id=str(item.id),
            description=item.description,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id
        )

        messages.success(
            self.request,
            _('Budget item "{}" added successfully!').format(item.description)
        )

        return redirect('budget:budget_overview', trip_pk=self.trip.pk)


class BudgetItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update budget item details."""
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'budget/item_form.html'

    def get_queryset(self):
        """Ensure user can only edit items they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return BudgetItem.objects.filter(trip__family__in=user_families)

    def get_form_kwargs(self):
        """Pass trip, creator, and family members to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.object.trip
        kwargs['created_by'] = self.request.user
        kwargs['family_members'] = User.objects.filter(
            family_memberships__family=self.object.trip.family
        ).distinct()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit {self.object.description}'
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "budget_item_updated",
            item_id=str(self.object.id),
            description=self.object.description,
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Budget item updated successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy('budget:budget_overview', kwargs={
            'trip_pk': self.object.trip.pk
        })


class BudgetItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a budget item."""
    model = BudgetItem
    template_name = 'budget/item_confirm_delete.html'

    def get_queryset(self):
        """Ensure only admins can delete items."""
        admin_families = Family.objects.filter(
            members__user=self.request.user,
            members__role__in=['owner', 'admin']
        )
        return BudgetItem.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to budget overview."""
        return reverse_lazy('budget:budget_overview', kwargs={
            'trip_pk': self.object.trip.pk
        })

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        item = self.get_object()
        logger.info(
            "budget_item_deleted",
            item_id=str(item.id),
            description=item.description,
            user_id=request.user.id
        )
        messages.success(request, _('Budget item deleted successfully.'))
        return super().delete(request, *args, **kwargs)
