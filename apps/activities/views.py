"""
Views for activity management.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
import structlog

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip
from .models import Activity
from .forms import ActivityForm, ActivityRatingForm

logger = structlog.get_logger(__name__)


class TripActivityListView(LoginRequiredMixin, ListView):
    """List all activities for a trip with sorting options."""
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'

    def get_queryset(self):
        """Return activities for the specified trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )

        queryset = Activity.objects.filter(trip=self.trip).select_related(
            'trip', 'created_by'
        )

        # Handle sorting
        sort_by = self.request.GET.get('sort', 'priority')
        if sort_by == 'priority':
            queryset = queryset.order_by('pre_trip_priority', '-created_at')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'distance':
            queryset = queryset.order_by('distance_from_resort', 'name')
        elif sort_by == 'cost':
            queryset = queryset.order_by('estimated_cost', 'name')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-post_trip_rating', 'name')
        elif sort_by == 'favorites':
            queryset = queryset.filter(is_favorite=True).order_by('name')

        return queryset

    def get_context_data(self, **kwargs):
        """Add trip and sorting context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['current_sort'] = self.request.GET.get('sort', 'priority')

        # Check if user can create activities
        try:
            membership = FamilyMember.objects.get(
                family=self.trip.family,
                user=self.request.user
            )
            context['can_create_activity'] = True  # All members can create
            context['can_edit'] = membership.is_admin() or self.trip.created_by == self.request.user
        except FamilyMember.DoesNotExist:
            context['can_create_activity'] = False
            context['can_edit'] = False

        return context


class ActivityDetailView(LoginRequiredMixin, DetailView):
    """Display activity details."""
    model = Activity
    template_name = 'activities/activity_detail.html'
    context_object_name = 'activity'

    def get_queryset(self):
        """Ensure user can only view activities from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return Activity.objects.filter(
            trip__family__in=user_families
        ).select_related('trip', 'created_by')

    def get_context_data(self, **kwargs):
        """Add permissions context."""
        context = super().get_context_data(**kwargs)
        activity = self.object

        # Check if user can edit/delete
        try:
            membership = FamilyMember.objects.get(
                family=activity.trip.family,
                user=self.request.user
            )
            # Admins and activity creator can edit
            context['can_edit'] = (
                membership.is_admin() or
                activity.created_by == self.request.user
            )
            context['can_delete'] = membership.is_admin()
            context['can_rate'] = True  # All members can rate
        except FamilyMember.DoesNotExist:
            context['can_edit'] = False
            context['can_delete'] = False
            context['can_rate'] = False

        return context


class ActivityCreateView(LoginRequiredMixin, CreateView):
    """Create a new activity."""
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add trip context."""
        from django.conf import settings
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'Add Activity to {self.trip.name}'
        context['mapbox_token'] = settings.MAPBOX_ACCESS_TOKEN

        # Add resort coordinates for distance calculation
        if hasattr(self.trip, 'resort') and self.trip.resort:
            resort = self.trip.resort
            if resort.latitude and resort.longitude:
                context['resort_latitude'] = float(resort.latitude)
                context['resort_longitude'] = float(resort.longitude)

        return context

    def form_valid(self, form):
        """Save the activity."""
        activity = form.save(commit=False)
        activity.trip = self.trip
        activity.created_by = self.request.user
        activity.save()

        logger.info(
            "activity_created",
            activity_id=str(activity.id),
            activity_name=activity.name,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id
        )

        messages.success(
            self.request,
            _('Activity "{}" added successfully!').format(activity.name)
        )

        return redirect('activities:activity_list', trip_pk=self.trip.pk)


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    """Update activity details."""
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'

    def get_queryset(self):
        """Ensure user can only edit activities they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return Activity.objects.filter(trip__family__in=user_families)

    def get_context_data(self, **kwargs):
        """Add context."""
        from django.conf import settings
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit {self.object.name}'
        context['mapbox_token'] = settings.MAPBOX_ACCESS_TOKEN

        # Add resort coordinates for distance calculation
        trip = self.object.trip
        if hasattr(trip, 'resort') and trip.resort:
            resort = trip.resort
            if resort.latitude and resort.longitude:
                context['resort_latitude'] = float(resort.latitude)
                context['resort_longitude'] = float(resort.longitude)

        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "activity_updated",
            activity_id=str(self.object.id),
            activity_name=self.object.name,
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Activity updated successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to activity list."""
        return reverse_lazy('activities:activity_list', kwargs={
            'trip_pk': self.object.trip.pk
        })


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an activity."""
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'

    def get_queryset(self):
        """Ensure only admins can delete activities."""
        admin_families = Family.objects.filter(
            members__user=self.request.user,
            members__role__in=['owner', 'admin']
        )
        return Activity.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to activity list."""
        return reverse_lazy('activities:activity_list', kwargs={
            'trip_pk': self.object.trip.pk
        })

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        activity = self.get_object()
        logger.info(
            "activity_deleted",
            activity_id=str(activity.id),
            activity_name=activity.name,
            user_id=request.user.id
        )
        messages.success(request, _('Activity deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@login_required
def rate_activity(request, pk):
    """Rate an activity after the trip."""
    # Get the activity and verify permissions
    user_families = Family.objects.filter(members__user=request.user)
    activity = get_object_or_404(
        Activity,
        pk=pk,
        trip__family__in=user_families
    )

    if request.method == 'POST':
        form = ActivityRatingForm(request.POST, instance=activity)
        if form.is_valid():
            activity = form.save()

            logger.info(
                "activity_rated",
                activity_id=str(activity.id),
                rating=activity.post_trip_rating,
                is_favorite=activity.is_favorite,
                user_id=request.user.id
            )

            messages.success(request, _('Activity rating saved!'))
            return redirect('activities:activity_detail', pk=activity.pk)
    else:
        form = ActivityRatingForm(instance=activity)

    return render(request, 'activities/activity_rating_form.html', {
        'form': form,
        'activity': activity,
    })


@login_required
def update_priority(request):
    """Update activity priority order via AJAX."""
    if request.method == 'POST':
        activity_id = request.POST.get('activity_id')
        new_priority = request.POST.get('priority')

        try:
            # Verify user has access to this activity
            user_families = Family.objects.filter(members__user=request.user)
            activity = Activity.objects.get(
                id=activity_id,
                trip__family__in=user_families
            )

            activity.pre_trip_priority = int(new_priority)
            activity.save()

            logger.info(
                "activity_priority_updated",
                activity_id=str(activity.id),
                new_priority=new_priority,
                user_id=request.user.id
            )

            return JsonResponse({'success': True})
        except Activity.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Activity not found'})
        except Exception as e:
            logger.error(
                "activity_priority_update_failed",
                error=str(e),
                user_id=request.user.id
            )
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})
