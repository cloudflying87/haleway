"""
Views for packing list management.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Prefetch
import structlog

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip
from .models import (
    PackingListTemplate,
    PackingListTemplateItem,
    TripPackingList,
    TripPackingItem
)
from .forms import (
    PackingListTemplateForm,
    TripPackingListForm,
    PackingItemForm,
    OutfitCalculatorForm
)

logger = structlog.get_logger(__name__)


# ============================================================================
# Template Management Views
# ============================================================================

class TemplateListView(LoginRequiredMixin, ListView):
    """List all packing list templates (system + user-created)."""
    model = PackingListTemplate
    template_name = 'packing/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        """Return system templates and user's custom templates."""
        return PackingListTemplate.objects.filter(
            Q(is_system_template=True) | Q(created_by=self.request.user)
        ).prefetch_related('items').order_by('-is_system_template', 'name')

    def get_context_data(self, **kwargs):
        """Add template categories to context."""
        context = super().get_context_data(**kwargs)
        templates = context['templates']
        context['system_templates'] = templates.filter(is_system_template=True)
        context['custom_templates'] = templates.filter(is_system_template=False)
        return context


class TemplateDetailView(LoginRequiredMixin, DetailView):
    """Display template details with all items."""
    model = PackingListTemplate
    template_name = 'packing/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        """Ensure user can only view system templates or their own."""
        return PackingListTemplate.objects.filter(
            Q(is_system_template=True) | Q(created_by=self.request.user)
        ).prefetch_related('items')

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

        context['items_by_category'] = items_by_category
        context['can_edit'] = not template.is_system_template and template.created_by == self.request.user
        context['can_delete'] = not template.is_system_template and template.created_by == self.request.user

        return context


class TemplateCreateView(LoginRequiredMixin, CreateView):
    """Create a new custom packing list template."""
    model = PackingListTemplate
    form_class = PackingListTemplateForm
    template_name = 'packing/template_form.html'

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
            user_id=self.request.user.id
        )

        messages.success(
            self.request,
            f'Template "{template.name}" created successfully! Now add items to it.'
        )
        return redirect('packing:template_detail', pk=template.pk)


class TemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a custom packing list template."""
    model = PackingListTemplate
    form_class = PackingListTemplateForm
    template_name = 'packing/template_form.html'

    def get_queryset(self):
        """Only allow editing user's own custom templates."""
        return PackingListTemplate.objects.filter(
            created_by=self.request.user,
            is_system_template=False
        )

    def form_valid(self, form):
        """Save the template."""
        template = form.save()

        logger.info(
            "packing_template_updated",
            template_id=str(template.id),
            template_name=template.name,
            user_id=self.request.user.id
        )

        messages.success(self.request, f'Template "{template.name}" updated successfully!')
        return redirect('packing:template_detail', pk=template.pk)


class TemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a custom packing list template."""
    model = PackingListTemplate
    template_name = 'packing/template_confirm_delete.html'
    success_url = reverse_lazy('packing:template_list')

    def get_queryset(self):
        """Only allow deleting user's own custom templates."""
        return PackingListTemplate.objects.filter(
            created_by=self.request.user,
            is_system_template=False
        )

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        template = self.get_object()
        template_name = template.name

        logger.info(
            "packing_template_deleted",
            template_id=str(template.id),
            template_name=template_name,
            user_id=request.user.id
        )

        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Trip Packing List Views
# ============================================================================

class TripPackingListListView(LoginRequiredMixin, ListView):
    """List all packing lists for a trip."""
    model = TripPackingList
    template_name = 'packing/trip_packing_lists.html'
    context_object_name = 'packing_lists'

    def get_queryset(self):
        """Return packing lists for the specified trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )

        return TripPackingList.objects.filter(trip=self.trip).select_related(
            'assigned_to', 'based_on_template'
        ).prefetch_related('items')

    def get_context_data(self, **kwargs):
        """Add trip and template context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip

        # Available templates for creating new lists
        context['templates'] = PackingListTemplate.objects.filter(
            Q(is_system_template=True) | Q(created_by=self.request.user)
        ).order_by('-is_system_template', 'name')

        # Family members for assignment
        context['family_members'] = self.trip.family.get_all_members()

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=self.trip.family,
                user=self.request.user
            )
            context['can_create'] = True
            context['can_edit'] = True
        except FamilyMember.DoesNotExist:
            context['can_create'] = False
            context['can_edit'] = False

        return context


class PackingListDetailView(LoginRequiredMixin, DetailView):
    """Display packing list details with items and progress."""
    model = TripPackingList
    template_name = 'packing/packing_list_detail.html'
    context_object_name = 'packing_list'

    def get_queryset(self):
        """Ensure user can only view lists from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return TripPackingList.objects.filter(
            trip__family__in=user_families
        ).select_related('trip', 'assigned_to', 'based_on_template').prefetch_related('items')

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

        context['items_by_category'] = items_by_category
        context['packed_percentage'] = packing_list.get_packed_percentage()
        context['packed_count'] = packing_list.get_packed_count()
        context['total_count'] = packing_list.get_total_count()

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=packing_list.trip.family,
                user=self.request.user
            )
            context['can_edit'] = True
            context['can_delete'] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context['can_edit'] = False
            context['can_delete'] = False

        return context


@login_required
def create_packing_list(request, trip_pk):
    """Create a new packing list from a template."""
    trip = get_object_or_404(
        Trip,
        pk=trip_pk,
        family__members__user=request.user
    )

    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        list_name = request.POST.get('list_name')
        assigned_to_id = request.POST.get('assigned_to')

        # Get the template
        template = get_object_or_404(
            PackingListTemplate,
            pk=template_id
        )

        # Get assigned user if specified
        assigned_to = None
        if assigned_to_id:
            from apps.accounts.models import User
            assigned_to = get_object_or_404(User, pk=assigned_to_id)

        # Create the packing list from template
        packing_list = template.duplicate_for_trip(
            trip=trip,
            assigned_to=assigned_to,
            list_name=list_name
        )

        messages.success(
            request,
            f'Packing list "{packing_list.name}" created successfully!'
        )
        return redirect('packing:list_detail', pk=packing_list.pk)

    # GET request - show template selection form
    templates = PackingListTemplate.objects.filter(
        Q(is_system_template=True) | Q(created_by=request.user)
    ).order_by('-is_system_template', 'name')

    # Separate system and custom templates for template display
    custom_templates = templates.filter(is_system_template=False)

    family_members = trip.family.get_all_members()

    return render(request, 'packing/create_packing_list.html', {
        'trip': trip,
        'templates': templates,
        'custom_templates': custom_templates,
        'family_members': family_members
    })


@login_required
def save_as_template(request, pk):
    """Save a trip packing list as a new template."""
    packing_list = get_object_or_404(
        TripPackingList,
        pk=pk,
        trip__family__members__user=request.user
    )

    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        description = request.POST.get('description', '')

        # Create the template
        template = packing_list.save_as_template(
            template_name=template_name,
            description=description
        )

        messages.success(
            request,
            f'Template "{template.name}" created successfully! You can now use it for future trips.'
        )
        return redirect('packing:template_detail', pk=template.pk)

    return render(request, 'packing/save_as_template.html', {
        'packing_list': packing_list
    })


class PackingListDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a packing list."""
    model = TripPackingList
    template_name = 'packing/packing_list_confirm_delete.html'

    def get_queryset(self):
        """Ensure user is admin of the family."""
        return TripPackingList.objects.filter(
            trip__family__members__user=self.request.user,
            trip__family__members__role__in=['owner', 'admin']
        )

    def get_success_url(self):
        """Return to trip packing lists."""
        return reverse('packing:trip_packing_lists', kwargs={'trip_pk': self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        packing_list = self.get_object()
        list_name = packing_list.name
        trip_pk = packing_list.trip.pk

        logger.info(
            "packing_list_deleted",
            packing_list_id=str(packing_list.id),
            list_name=list_name,
            trip_id=str(trip_pk),
            user_id=request.user.id
        )

        messages.success(request, f'Packing list "{list_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Packing Item Management
# ============================================================================

@login_required
def add_packing_item(request, list_pk):
    """Add a new item to a packing list."""
    packing_list = get_object_or_404(
        TripPackingList,
        pk=list_pk,
        trip__family__members__user=request.user
    )

    if request.method == 'POST':
        form = PackingItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.packing_list = packing_list
            item.save()

            logger.info(
                "packing_item_added",
                item_id=str(item.id),
                item_name=item.item_name,
                packing_list_id=str(packing_list.id),
                user_id=request.user.id
            )

            messages.success(request, f'Item "{item.item_name}" added successfully!')
            return redirect('packing:list_detail', pk=packing_list.pk)
    else:
        form = PackingItemForm()

    return render(request, 'packing/add_item.html', {
        'packing_list': packing_list,
        'form': form
    })


@login_required
def toggle_packed(request, pk):
    """Toggle the packed status of an item (AJAX)."""
    item = get_object_or_404(
        TripPackingItem,
        pk=pk,
        packing_list__trip__family__members__user=request.user
    )

    item.is_packed = not item.is_packed
    item.save()

    logger.info(
        "packing_item_toggled",
        item_id=str(item.id),
        item_name=item.item_name,
        is_packed=item.is_packed,
        user_id=request.user.id
    )

    return JsonResponse({
        'success': True,
        'is_packed': item.is_packed,
        'packed_count': item.packing_list.get_packed_count(),
        'total_count': item.packing_list.get_total_count(),
        'percentage': item.packing_list.get_packed_percentage()
    })


@login_required
def edit_packing_item(request, pk):
    """Edit a packing item."""
    item = get_object_or_404(
        TripPackingItem,
        pk=pk,
        packing_list__trip__family__members__user=request.user
    )

    if request.method == 'POST':
        form = PackingItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()

            logger.info(
                "packing_item_updated",
                item_id=str(item.id),
                item_name=item.item_name,
                user_id=request.user.id
            )

            messages.success(request, f'Item "{item.item_name}" updated successfully!')
            return redirect('packing:list_detail', pk=item.packing_list.pk)
    else:
        form = PackingItemForm(instance=item)

    return render(request, 'packing/edit_item.html', {
        'item': item,
        'form': form
    })


@login_required
def delete_packing_item(request, pk):
    """Delete a packing item."""
    item = get_object_or_404(
        TripPackingItem,
        pk=pk,
        packing_list__trip__family__members__user=request.user
    )

    packing_list = item.packing_list
    item_name = item.item_name

    if request.method == 'POST':
        item.delete()

        logger.info(
            "packing_item_deleted",
            item_id=str(pk),
            item_name=item_name,
            packing_list_id=str(packing_list.id),
            user_id=request.user.id
        )

        messages.success(request, f'Item "{item_name}" deleted successfully!')
        return redirect('packing:list_detail', pk=packing_list.pk)

    return render(request, 'packing/delete_item.html', {
        'item': item
    })


# ============================================================================
# Outfit Calculator
# ============================================================================

@login_required
def add_outfit(request, list_pk):
    """Add clothing items based on number of outfits."""
    packing_list = get_object_or_404(
        TripPackingList,
        pk=list_pk,
        trip__family__members__user=request.user
    )

    if request.method == 'POST':
        form = OutfitCalculatorForm(request.POST)
        if form.is_valid():
            num_outfits = form.cleaned_data['num_outfits']

            # Define outfit items with their quantities
            # For example: 5 outfits = 5 shirts, 3 pants, 5 underwear, 5 socks
            outfit_items = [
                ('Clothing', 'Shirts', num_outfits, ''),
                ('Clothing', 'Pants', max(3, num_outfits // 2), 'Mix and match'),
                ('Clothing', 'Underwear', num_outfits, ''),
                ('Clothing', 'Socks', num_outfits, ''),
                ('Clothing', 'Pajamas', 2, ''),
            ]

            # Get current max order for clothing items
            max_order = TripPackingItem.objects.filter(
                packing_list=packing_list,
                category='Clothing'
            ).count()

            # Create the items
            for order, (category, item_name, qty, notes) in enumerate(outfit_items, start=max_order + 1):
                TripPackingItem.objects.create(
                    packing_list=packing_list,
                    category=category,
                    item_name=item_name,
                    quantity=qty,
                    notes=notes,
                    order=order
                )

            logger.info(
                "outfit_items_added",
                num_outfits=num_outfits,
                packing_list_id=str(packing_list.id),
                items_added=len(outfit_items),
                user_id=request.user.id
            )

            messages.success(
                request,
                f'Added clothing items for {num_outfits} outfits successfully!'
            )
            return redirect('packing:list_detail', pk=packing_list.pk)
    else:
        form = OutfitCalculatorForm()

    return render(request, 'packing/add_outfit.html', {
        'packing_list': packing_list,
        'form': form
    })
