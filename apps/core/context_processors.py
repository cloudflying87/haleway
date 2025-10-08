"""
Context processors for making data available in all templates.
"""

import structlog

from apps.trips.models import Trip

logger = structlog.get_logger(__name__)


def current_trip(request):
    """
    Make the user's current trip available in all templates.

    The current trip is determined by:
    1. Session variable 'current_trip_id' if set
    2. Otherwise, the next upcoming trip for the user
    3. If no upcoming trips, the most recently created trip
    """
    if not request.user.is_authenticated:
        return {"current_trip": None}

    current_trip_obj = None

    # Try to get from session first
    current_trip_id = request.session.get("current_trip_id")
    if current_trip_id:
        try:
            # Verify user has access to this trip
            current_trip_obj = Trip.objects.filter(
                pk=current_trip_id, family__members__user=request.user
            ).first()

            if not current_trip_obj:
                # Trip no longer exists or user lost access, clear session
                logger.warning(
                    "current_trip_not_accessible", user_id=request.user.id, trip_id=current_trip_id
                )
                del request.session["current_trip_id"]
        except Exception as e:
            logger.error(
                "current_trip_lookup_error",
                user_id=request.user.id,
                trip_id=current_trip_id,
                error=str(e),
            )
            del request.session["current_trip_id"]

    # If no current trip in session, find next upcoming trip
    if not current_trip_obj:
        # Try to find next upcoming trip (starts in the future or is currently active)
        current_trip_obj = (
            Trip.objects.filter(
                family__members__user=request.user, status__in=["planning", "active"]
            )
            .order_by("start_date")
            .first()
        )

        # If no upcoming trips, get most recent trip
        if not current_trip_obj:
            current_trip_obj = (
                Trip.objects.filter(family__members__user=request.user)
                .order_by("-start_date")
                .first()
            )

    return {"current_trip": current_trip_obj}
