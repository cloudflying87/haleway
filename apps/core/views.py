"""
Core app views.
"""

import json

import structlog
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.families.models import Family
from apps.trips.models import Resort, Trip

logger = structlog.get_logger(__name__)


def home(request):
    """Homepage view - shows dashboard for authenticated users, landing page for others."""

    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    # Show landing page for non-authenticated users
    context = {
        "project_name": "haleway",
    }
    return render(request, "core/landing.html", context)


def dashboard(request):
    """Dashboard view for authenticated users showing trip overview."""
    context = {}

    # Get user's families
    user_families = Family.objects.filter(members__user=request.user)

    # Get current date
    today = timezone.now().date()

    # Get active trip (trip happening right now)
    active_trip = (
        Trip.objects.filter(family__in=user_families, start_date__lte=today, end_date__gte=today)
        .select_related("family")
        .prefetch_related("resort")
        .first()
    )

    # Get upcoming trips (future trips)
    upcoming_trips_qs = (
        Trip.objects.filter(family__in=user_families, start_date__gt=today)
        .select_related("family")
        .prefetch_related("resort")
        .order_by("start_date")[:5]
    )

    # Add days_until to each trip
    upcoming_trips = []
    for trip in upcoming_trips_qs:
        trip.days_until = (trip.start_date - today).days
        upcoming_trips.append(trip)

    # Get recent/past trips
    past_trips = (
        Trip.objects.filter(family__in=user_families, end_date__lt=today)
        .select_related("family")
        .prefetch_related("resort")
        .order_by("-end_date")[:3]
    )

    # Get stats
    context["active_trip"] = active_trip
    context["upcoming_trips"] = upcoming_trips
    context["past_trips"] = past_trips
    context["total_trips"] = Trip.objects.filter(family__in=user_families).count()
    context["families_count"] = user_families.count()

    # Get resort for active trip if exists
    if active_trip:
        try:
            context["active_resort"] = active_trip.resort
        except Resort.DoesNotExist:
            context["active_resort"] = None

    return render(request, "core/dashboard.html", context)


@login_required
@require_http_methods(["GET"])
def get_user_trips(request):
    """
    API endpoint to get user's trips for trip switcher.
    Returns JSON list of trips with metadata.
    """
    try:
        # Get user's families
        user_families = Family.objects.filter(members__user=request.user)

        # Get all user's trips
        trips = (
            Trip.objects.filter(family__in=user_families)
            .select_related("family")
            .order_by("-start_date")
        )

        # Get current trip ID from session
        current_trip_id = request.session.get("current_trip_id")

        # Build trip list
        trip_list = []
        for trip in trips:
            trip_list.append(
                {
                    "id": str(trip.pk),
                    "name": trip.name,
                    "destination": trip.destination_name,
                    "date_range": f"{trip.start_date.strftime('%b %d, %Y')} - {trip.end_date.strftime('%b %d, %Y')}",
                    "status": trip.status,
                    "is_current": str(trip.pk) == str(current_trip_id)
                    if current_trip_id
                    else False,
                }
            )

        logger.info("user_trips_fetched", user_id=request.user.id, trip_count=len(trip_list))

        return JsonResponse({"success": True, "trips": trip_list})

    except Exception as e:
        logger.error("get_user_trips_error", user_id=request.user.id, error=str(e), exc_info=True)
        return JsonResponse({"success": False, "error": "Failed to load trips"}, status=500)


@login_required
@require_http_methods(["POST"])
def set_current_trip(request):
    """
    API endpoint to set the current trip in session.
    Expects JSON body: {"trip_id": "uuid"}
    """
    try:
        data = json.loads(request.body)
        trip_id = data.get("trip_id")

        if not trip_id:
            return JsonResponse({"success": False, "error": "trip_id is required"}, status=400)

        # Verify user has access to this trip
        trip = Trip.objects.filter(pk=trip_id, family__members__user=request.user).first()

        if not trip:
            logger.warning(
                "set_current_trip_unauthorized", user_id=request.user.id, trip_id=trip_id
            )
            return JsonResponse(
                {"success": False, "error": "Trip not found or access denied"}, status=404
            )

        # Set in session
        request.session["current_trip_id"] = str(trip_id)

        logger.info(
            "current_trip_set", user_id=request.user.id, trip_id=trip_id, trip_name=trip.name
        )

        return JsonResponse({"success": True, "trip_name": trip.name})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error("set_current_trip_error", user_id=request.user.id, error=str(e), exc_info=True)
        return JsonResponse({"success": False, "error": "Failed to set current trip"}, status=500)
