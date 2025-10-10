"""
Views for trip management.
"""

import structlog
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.families.models import Family, FamilyMember
from apps.packing.weather import WeatherService

from .forms import ResortForm, TripForm, TripResortForm
from .models import Resort, Trip

logger = structlog.get_logger(__name__)


class TripListView(LoginRequiredMixin, ListView):
    """List all trips for families the user is a member of."""

    model = Trip
    template_name = "trips/trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        """Return trips for families the user belongs to."""
        return (
            Trip.objects.filter(family__members__user=self.request.user)
            .select_related("family", "created_by")
            .prefetch_related("resort")
            .order_by("-start_date")
        )

    def get_context_data(self, **kwargs):
        """Add family context."""
        context = super().get_context_data(**kwargs)
        # Get user's families for the "create trip" dropdown
        context["user_families"] = Family.objects.filter(members__user=self.request.user).distinct()
        return context


class DreamTripsListView(LoginRequiredMixin, ListView):
    """List dream trips (wishlist) for families the user is a member of."""

    model = Trip
    template_name = "trips/dream_trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        """Return only dream trips for families the user belongs to."""
        return (
            Trip.objects.filter(family__members__user=self.request.user, status="dream")
            .select_related("family", "created_by")
            .prefetch_related("resort")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        """Add family context."""
        context = super().get_context_data(**kwargs)
        # Get user's families for the "create trip" dropdown
        context["user_families"] = Family.objects.filter(members__user=self.request.user).distinct()
        return context


class ResortsListView(LoginRequiredMixin, ListView):
    """List all resorts for trips the user is a member of."""

    model = Resort
    template_name = "trips/resort_list.html"
    context_object_name = "resorts"

    def get_queryset(self):
        """Return resorts for trips in families the user belongs to."""
        return (
            Resort.objects.filter(trip__family__members__user=self.request.user)
            .select_related("trip", "trip__family")
            .order_by("-trip__start_date")
        )

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        return context


class FamilyTripListView(LoginRequiredMixin, ListView):
    """List trips for a specific family."""

    model = Trip
    template_name = "trips/family_trip_list.html"
    context_object_name = "trips"

    def get_queryset(self):
        """Return trips for the specified family."""
        self.family = get_object_or_404(
            Family, pk=self.kwargs["family_pk"], members__user=self.request.user
        )
        return (
            Trip.objects.filter(family=self.family)
            .select_related("created_by")
            .prefetch_related("resort")
            .order_by("-start_date")
        )

    def get_context_data(self, **kwargs):
        """Add family context."""
        context = super().get_context_data(**kwargs)
        context["family"] = self.family

        # Check if user can create trips
        try:
            membership = FamilyMember.objects.get(family=self.family, user=self.request.user)
            context["can_create_trip"] = True  # All members can create trips
        except FamilyMember.DoesNotExist:
            context["can_create_trip"] = False

        return context


class TripDetailView(LoginRequiredMixin, DetailView):
    """Display trip details."""

    model = Trip
    template_name = "trips/trip_detail.html"
    context_object_name = "trip"

    def get_queryset(self):
        """Ensure user can only view trips from their families."""
        return (
            Trip.objects.filter(family__members__user=self.request.user)
            .select_related("family", "created_by")
            .prefetch_related("resort")
        )

    def get(self, request, *args, **kwargs):
        """Override to set this trip as the current trip in session."""
        response = super().get(request, *args, **kwargs)

        # Automatically set this trip as the current trip
        trip = self.object
        request.session["current_trip_id"] = str(trip.pk)

        logger.info(
            "trip_detail_viewed",
            user_id=request.user.id,
            trip_id=str(trip.pk),
            trip_name=trip.name,
            auto_set_current=True,
        )

        return response

    def get_context_data(self, **kwargs):
        """Add permissions context."""
        context = super().get_context_data(**kwargs)
        trip = self.object

        # Check if user can edit/delete
        try:
            membership = FamilyMember.objects.get(family=trip.family, user=self.request.user)
            # All family members can edit/create content
            context["can_edit"] = True
            context["can_delete"] = membership.is_admin()
            context["can_create_note"] = True  # All members can create notes
        except FamilyMember.DoesNotExist:
            context["can_edit"] = False
            context["can_delete"] = False
            context["can_create_note"] = False

        # Get resort if exists
        try:
            context["resort"] = trip.resort
        except Resort.DoesNotExist:
            context["resort"] = None

        # Get weather forecast if resort has coordinates
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

                # Build Weather Underground URL
                if resort.city and resort.state:
                    city_clean = resort.city.lower().replace(" ", "-")
                    state_clean = resort.state.lower()
                    country_clean = (resort.country or "us").lower()
                    context["wunderground_url"] = (
                        f"https://www.wunderground.com/weather/{country_clean}/"
                        f"{state_clean}/{city_clean}"
                    )
                else:
                    context["wunderground_url"] = (
                        f"https://www.wunderground.com/weather/{resort.latitude},{resort.longitude}"
                    )

                if weather_forecast:
                    # Calculate temperature range
                    highs = [day["high"] for day in weather_forecast if day["high"] is not None]
                    lows = [day["low"] for day in weather_forecast if day["low"] is not None]
                    if highs and lows:
                        context["temp_range"] = {"high": max(highs), "low": min(lows)}

        # Get recent notes for this trip (up to 5)
        from apps.notes.forms import NoteForm
        from apps.notes.models import Note, NoteCategory

        context["recent_notes"] = Note.objects.filter(trip=trip).select_related(
            "category", "created_by"
        )[:5]
        context["note_count"] = Note.objects.filter(trip=trip).count()

        # Add note form for modal
        context["note_form"] = NoteForm(trip=trip, created_by=self.request.user)
        context["categories"] = NoteCategory.objects.filter(trip=trip)

        # Add activity form for modal
        from apps.activities.forms import ActivityForm

        context["activity_form"] = ActivityForm()

        # Add mapbox token and resort coordinates for activity form
        from django.conf import settings

        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN
        if hasattr(trip, "resort") and trip.resort:
            resort = trip.resort
            if resort.latitude and resort.longitude:
                context["resort_latitude"] = float(resort.latitude)
                context["resort_longitude"] = float(resort.longitude)

        # Get recent activities for this trip (up to 5, ordered by priority)
        from apps.activities.models import Activity

        context["recent_activities"] = (
            Activity.objects.filter(trip=trip)
            .select_related("created_by")
            .order_by("pre_trip_priority", "-created_at")[:5]
        )
        context["activity_count"] = Activity.objects.filter(trip=trip).count()

        # Get budget summary for this trip
        from decimal import Decimal

        from django.db.models import Sum

        from apps.budget.models import BudgetItem

        budget_items = BudgetItem.objects.filter(trip=trip).select_related(
            "category", "paid_by", "created_by"
        )[:5]
        context["recent_budget_items"] = budget_items
        context["budget_item_count"] = BudgetItem.objects.filter(trip=trip).count()

        # Calculate budget totals
        all_budget_items = BudgetItem.objects.filter(trip=trip)
        context["budget_total_estimated"] = all_budget_items.aggregate(
            total=Sum("estimated_amount")
        )["total"] or Decimal("0.00")
        context["budget_total_actual"] = all_budget_items.aggregate(total=Sum("actual_amount"))[
            "total"
        ] or Decimal("0.00")
        context["budget_variance"] = (
            context["budget_total_estimated"] - context["budget_total_actual"]
        )

        # Get upcoming itinerary items for this trip (up to 5, ordered by date)
        from django.utils import timezone

        from apps.itinerary.models import DailyItinerary

        today = timezone.now().date()
        context["upcoming_itinerary"] = (
            DailyItinerary.objects.filter(trip=trip, date__gte=today)
            .select_related("activity", "created_by")
            .order_by("date", "time_start", "order")[:5]
        )
        context["itinerary_count"] = DailyItinerary.objects.filter(trip=trip).count()

        # Get recent photos for this trip (up to 6 for gallery preview)
        from apps.memories.models import DailyJournal, TripPhoto

        context["recent_photos"] = (
            TripPhoto.objects.filter(trip=trip)
            .select_related("uploaded_by")
            .order_by("-taken_date", "-uploaded_at")[:6]
        )
        context["photo_count"] = TripPhoto.objects.filter(trip=trip).count()

        # Get recent journal entries for this trip (up to 3)
        context["recent_journals"] = (
            DailyJournal.objects.filter(trip=trip)
            .select_related("created_by")
            .order_by("-date")[:3]
        )
        context["journal_count"] = DailyJournal.objects.filter(trip=trip).count()

        # Get packing list for this trip (one per trip)
        from apps.packing.models import TripPackingList

        try:
            context["packing_list"] = (
                TripPackingList.objects.select_related("based_on_template")
                .prefetch_related("items")
                .get(trip=trip)
            )
        except TripPackingList.DoesNotExist:
            context["packing_list"] = None

        # Get grocery lists for this trip (up to 5)
        from apps.grocery.models import TripGroceryList

        context["grocery_lists"] = (
            TripGroceryList.objects.filter(trip=trip)
            .select_related("assigned_to", "based_on_template")
            .prefetch_related("items")[:5]
        )
        context["grocery_lists_count"] = TripGroceryList.objects.filter(trip=trip).count()

        return context


class TripCreateView(LoginRequiredMixin, CreateView):
    """Create a new trip."""

    model = Trip
    form_class = TripResortForm
    template_name = "trips/trip_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.family = get_object_or_404(
            Family, pk=self.kwargs["family_pk"], members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Override to prevent passing instance to regular Form."""
        kwargs = super().get_form_kwargs()
        # TripResortForm is a regular Form, not ModelForm, so remove instance
        kwargs.pop("instance", None)
        return kwargs

    def get_context_data(self, **kwargs):
        """Add family context."""
        context = super().get_context_data(**kwargs)
        context["family"] = self.family
        context["page_title"] = f"Create Trip for {self.family.name}"
        return context

    def form_valid(self, form):
        """Save the trip and optional resort."""
        with transaction.atomic():
            # Create the trip
            trip = Trip.objects.create(
                family=self.family,
                name=form.cleaned_data["trip_name"],
                destination_name=form.cleaned_data["destination_name"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                status="planning",
                created_by=self.request.user,
            )

            # Create resort if name was provided
            resort_name = form.cleaned_data.get("resort_name")
            if resort_name:
                Resort.objects.create(
                    trip=trip,
                    name=resort_name,
                    website_url=form.cleaned_data.get("resort_website", ""),
                )

            logger.info(
                "trip_created",
                trip_id=str(trip.id),
                trip_name=trip.name,
                family_id=str(self.family.id),
                user_id=self.request.user.id,
            )

            messages.success(self.request, _('Trip "{}" created successfully!').format(trip.name))

            self.object = trip
            return redirect("trips:trip_detail", pk=trip.pk)


class TripUpdateView(LoginRequiredMixin, UpdateView):
    """Update trip details."""

    model = Trip
    form_class = TripForm
    template_name = "trips/trip_form.html"

    def get_queryset(self):
        """Ensure user can only edit trips they have permission for."""
        return Trip.objects.filter(family__members__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "trip_updated",
            trip_id=str(self.object.id),
            trip_name=self.object.name,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Trip updated successfully!"))
        return super().form_valid(form)


@login_required
def edit_resort(request, trip_pk):
    """Edit or create resort details for a trip."""
    # Get the trip and verify permissions
    trip = get_object_or_404(Trip, pk=trip_pk, family__members__user=request.user)

    # Get or create resort
    try:
        resort = trip.resort
    except Resort.DoesNotExist:
        resort = None

    if request.method == "POST":
        form = ResortForm(request.POST, instance=resort)
        if form.is_valid():
            resort = form.save(commit=False)
            resort.trip = trip
            resort.save()

            logger.info(
                "resort_updated",
                trip_id=str(trip.id),
                resort_id=str(resort.id),
                user_id=request.user.id,
            )

            messages.success(request, _("Resort details saved!"))
            return redirect("trips:trip_detail", pk=trip.pk)
    else:
        form = ResortForm(instance=resort)

    from django.conf import settings

    return render(
        request,
        "trips/resort_form.html",
        {
            "form": form,
            "trip": trip,
            "resort": resort,
            "mapbox_token": settings.MAPBOX_ACCESS_TOKEN,
        },
    )


class TripDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a trip."""

    model = Trip
    template_name = "trips/trip_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete trips."""
        return Trip.objects.filter(
            family__members__user=self.request.user,
            family__members__role__in=["owner", "admin"],
        )

    def get_success_url(self):
        """Redirect to family's trip list."""
        return reverse_lazy("trips:family_trip_list", kwargs={"family_pk": self.object.family.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        trip = self.get_object()
        logger.info(
            "trip_deleted", trip_id=str(trip.id), trip_name=trip.name, user_id=request.user.id
        )
        messages.success(request, _("Trip deleted successfully."))
        return super().delete(request, *args, **kwargs)


@login_required
def trip_weather(request, pk):
    """Display detailed weather forecast for a trip."""
    # Get the trip and verify permissions
    trip = get_object_or_404(Trip, pk=pk, family__members__user=request.user)

    # Get weather forecast if resort has coordinates
    weather_forecast = None
    temp_range = None
    wunderground_url = None

    if hasattr(trip, "resort") and trip.resort:
        resort = trip.resort
        if resort.latitude and resort.longitude:
            weather_forecast = WeatherService.get_forecast(
                latitude=float(resort.latitude),
                longitude=float(resort.longitude),
                start_date=trip.start_date,
                end_date=trip.end_date,
            )

            # Build Weather Underground URL
            # Try to use city/state if available, otherwise use coordinates
            if resort.city and resort.state:
                # Clean city name for URL (replace spaces with hyphens, lowercase)
                city_clean = resort.city.lower().replace(" ", "-")
                state_clean = resort.state.lower()
                country_clean = (resort.country or "us").lower()
                wunderground_url = (
                    f"https://www.wunderground.com/weather/{country_clean}/"
                    f"{state_clean}/{city_clean}"
                )
            else:
                # Use coordinates as fallback
                wunderground_url = (
                    f"https://www.wunderground.com/weather/{resort.latitude},{resort.longitude}"
                )

            if weather_forecast:
                # Calculate temperature range
                highs = [day["high"] for day in weather_forecast if day["high"] is not None]
                lows = [day["low"] for day in weather_forecast if day["low"] is not None]
                # Check for rain in forecast
                has_rain = any(day.get("weather_code", 0) >= 51 for day in weather_forecast)

                if highs and lows:
                    temp_range = {
                        "high": max(highs),
                        "low": min(lows),
                        "avg_high": round(sum(highs) / len(highs)),
                        "avg_low": round(sum(lows) / len(lows)),
                        "has_rain": has_rain,
                    }

    return render(
        request,
        "trips/trip_weather.html",
        {
            "trip": trip,
            "resort": trip.resort if hasattr(trip, "resort") else None,
            "weather_forecast": weather_forecast,
            "temp_range": temp_range,
            "wunderground_url": wunderground_url,
        },
    )
