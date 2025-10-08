"""
Views for itinerary management.
"""
from datetime import timedelta, date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
import structlog

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip
from apps.activities.models import Activity
from .models import DailyItinerary
from .forms import ItineraryItemForm, QuickAddEventForm, AssignActivityForm

logger = structlog.get_logger(__name__)


class TripCalendarView(LoginRequiredMixin, DetailView):
    """Calendar view showing all days of a trip with scheduled items."""
    model = Trip
    template_name = 'itinerary/calendar.html'
    context_object_name = 'trip'
    pk_url_kwarg = 'trip_pk'

    def get_queryset(self):
        """Ensure user can only view trips from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return Trip.objects.filter(family__in=user_families)

    def get_context_data(self, **kwargs):
        """Add calendar data."""
        context = super().get_context_data(**kwargs)
        trip = self.object

        # Generate list of all trip dates
        trip_days = []
        current_date = trip.start_date
        while current_date <= trip.end_date:
            # Get itinerary items for this day
            items = DailyItinerary.objects.filter(
                trip=trip,
                date=current_date
            ).select_related('activity', 'created_by').order_by('time_start', 'order')

            trip_days.append({
                'date': current_date,
                'items': items,
                'item_count': items.count(),
                'is_today': current_date == date.today(),
            })
            current_date += timedelta(days=1)

        context['trip_days'] = trip_days
        context['total_days'] = len(trip_days)

        # Get unscheduled activities
        scheduled_activity_ids = DailyItinerary.objects.filter(
            trip=trip,
            activity__isnull=False
        ).values_list('activity_id', flat=True)

        context['unscheduled_activities'] = Activity.objects.filter(
            trip=trip
        ).exclude(id__in=scheduled_activity_ids).order_by('pre_trip_priority', 'name')

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=trip.family,
                user=self.request.user
            )
            context['can_edit'] = True  # All members can add to itinerary
        except FamilyMember.DoesNotExist:
            context['can_edit'] = False

        return context


class DayDetailView(LoginRequiredMixin, ListView):
    """Detailed timeline view for a specific day."""
    model = DailyItinerary
    template_name = 'itinerary/day_detail.html'
    context_object_name = 'items'

    def get_queryset(self):
        """Get itinerary items for this specific day."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )
        self.date = date.fromisoformat(self.kwargs['date'])

        return DailyItinerary.objects.filter(
            trip=self.trip,
            date=self.date
        ).select_related('activity', 'created_by').order_by('time_start', 'order')

    def get_context_data(self, **kwargs):
        """Add day context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['date'] = self.date
        context['day_number'] = (self.date - self.trip.start_date).days + 1

        # Get prev/next days
        if self.date > self.trip.start_date:
            context['prev_date'] = self.date - timedelta(days=1)
        if self.date < self.trip.end_date:
            context['next_date'] = self.date + timedelta(days=1)

        # Check permissions
        try:
            membership = FamilyMember.objects.get(
                family=self.trip.family,
                user=self.request.user
            )
            context['can_edit'] = True
        except FamilyMember.DoesNotExist:
            context['can_edit'] = False

        # Get unscheduled activities for quick-add
        scheduled_activity_ids = DailyItinerary.objects.filter(
            trip=self.trip,
            activity__isnull=False
        ).values_list('activity_id', flat=True)

        context['unscheduled_activities'] = Activity.objects.filter(
            trip=self.trip
        ).exclude(id__in=scheduled_activity_ids).order_by('pre_trip_priority', 'name')

        return context


class ItineraryItemCreateView(LoginRequiredMixin, CreateView):
    """Create a new itinerary item."""
    model = DailyItinerary
    form_class = ItineraryItemForm
    template_name = 'itinerary/item_form.html'

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

    def get_initial(self):
        """Pre-fill date if provided."""
        initial = super().get_initial()
        if 'date' in self.kwargs:
            initial['date'] = self.kwargs['date']
        return initial

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'Add to Itinerary - {self.trip.name}'
        return context

    def form_valid(self, form):
        """Save the itinerary item."""
        item = form.save(commit=False)
        item.trip = self.trip
        item.created_by = self.request.user
        item.save()

        logger.info(
            "itinerary_item_created",
            item_id=str(item.id),
            trip_id=str(self.trip.id),
            date=str(item.date),
            user_id=self.request.user.id
        )

        messages.success(
            self.request,
            _('Added to itinerary for {}').format(item.date.strftime('%B %d'))
        )

        return redirect('itinerary:day_detail', trip_pk=self.trip.pk, date=item.date.isoformat())


class ItineraryItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update itinerary item details."""
    model = DailyItinerary
    form_class = ItineraryItemForm
    template_name = 'itinerary/item_form.html'

    def get_queryset(self):
        """Ensure user can only edit items from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return DailyItinerary.objects.filter(trip__family__in=user_families)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.object.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit - {self.object.get_display_title()}'
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "itinerary_item_updated",
            item_id=str(self.object.id),
            trip_id=str(self.object.trip.id),
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Itinerary item updated!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to day detail."""
        return reverse_lazy('itinerary:day_detail', kwargs={
            'trip_pk': self.object.trip.pk,
            'date': self.object.date.isoformat()
        })


class ItineraryItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an itinerary item."""
    model = DailyItinerary
    template_name = 'itinerary/item_confirm_delete.html'

    def get_queryset(self):
        """Ensure user can only delete items from their families."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return DailyItinerary.objects.filter(trip__family__in=user_families)

    def get_success_url(self):
        """Redirect to day detail."""
        return reverse_lazy('itinerary:day_detail', kwargs={
            'trip_pk': self.object.trip.pk,
            'date': self.object.date.isoformat()
        })

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        item = self.get_object()
        logger.info(
            "itinerary_item_deleted",
            item_id=str(item.id),
            trip_id=str(item.trip.id),
            user_id=request.user.id
        )
        messages.success(request, _('Removed from itinerary.'))
        return super().delete(request, *args, **kwargs)


@login_required
def quick_add_event(request, trip_pk, date=None):
    """Quick-add a standalone event (not linked to activity)."""
    # Get trip and verify permissions
    trip = get_object_or_404(
        Trip,
        pk=trip_pk,
        family__members__user=request.user
    )

    # Parse date if provided
    event_date = None
    if date:
        event_date = date if isinstance(date, date) else date.fromisoformat(date)

    if request.method == 'POST':
        form = QuickAddEventForm(request.POST, trip=trip, date=event_date)
        if form.is_valid():
            # Create the itinerary item
            item = DailyItinerary.objects.create(
                trip=trip,
                title=form.cleaned_data['title'],
                date=form.cleaned_data['date'],
                time_start=form.cleaned_data.get('time_start'),
                time_end=form.cleaned_data.get('time_end'),
                notes=form.cleaned_data.get('notes', ''),
                created_by=request.user
            )

            logger.info(
                "quick_event_added",
                item_id=str(item.id),
                trip_id=str(trip.id),
                title=item.title,
                user_id=request.user.id
            )

            messages.success(request, _(f'Added "{item.title}" to itinerary!'))
            return redirect('itinerary:day_detail', trip_pk=trip.pk, date=item.date.isoformat())
    else:
        form = QuickAddEventForm(trip=trip, date=event_date)

    return render(request, 'itinerary/quick_add_event.html', {
        'form': form,
        'trip': trip,
        'date': event_date,
    })


@login_required
def assign_activity(request, trip_pk, activity_pk):
    """Assign an existing activity to a specific day/time."""
    # Get trip and activity, verify permissions
    trip = get_object_or_404(
        Trip,
        pk=trip_pk,
        family__members__user=request.user
    )
    activity = get_object_or_404(Activity, pk=activity_pk, trip=trip)

    # Check if already scheduled
    existing = DailyItinerary.objects.filter(trip=trip, activity=activity).first()
    if existing:
        messages.warning(request, _(f'{activity.name} is already scheduled on {existing.date}'))
        return redirect('itinerary:day_detail', trip_pk=trip.pk, date=existing.date.isoformat())

    if request.method == 'POST':
        form = AssignActivityForm(request.POST, trip=trip)
        if form.is_valid():
            # Create the itinerary item
            item = DailyItinerary.objects.create(
                trip=trip,
                activity=activity,
                date=form.cleaned_data['date'],
                time_start=form.cleaned_data.get('time_start'),
                time_end=form.cleaned_data.get('time_end'),
                notes=form.cleaned_data.get('notes', ''),
                created_by=request.user
            )

            logger.info(
                "activity_assigned",
                item_id=str(item.id),
                activity_id=str(activity.id),
                trip_id=str(trip.id),
                date=str(item.date),
                user_id=request.user.id
            )

            messages.success(request, _(f'Scheduled {activity.name} for {item.date.strftime("%B %d")}!'))
            return redirect('itinerary:day_detail', trip_pk=trip.pk, date=item.date.isoformat())
    else:
        form = AssignActivityForm(trip=trip)

    return render(request, 'itinerary/assign_activity.html', {
        'form': form,
        'trip': trip,
        'activity': activity,
    })
