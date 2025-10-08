"""
Core app views.
"""
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count
from apps.trips.models import Trip
from apps.families.models import Family


def home(request):
    """Homepage view - shows dashboard for authenticated users, landing page for others."""

    # Redirect authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    # Show landing page for non-authenticated users
    context = {
        'project_name': 'haleway',
    }
    return render(request, 'core/landing.html', context)


def dashboard(request):
    """Dashboard view for authenticated users showing trip overview."""
    context = {}

    # Get user's families
    user_families = Family.objects.filter(members__user=request.user)

    # Get current date
    today = timezone.now().date()

    # Get active trip (trip happening right now)
    active_trip = Trip.objects.filter(
        family__in=user_families,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('family').prefetch_related('resort').first()

    # Get upcoming trips (future trips)
    upcoming_trips = Trip.objects.filter(
        family__in=user_families,
        start_date__gt=today
    ).select_related('family').prefetch_related('resort').order_by('start_date')[:5]

    # Get recent/past trips
    past_trips = Trip.objects.filter(
        family__in=user_families,
        end_date__lt=today
    ).select_related('family').prefetch_related('resort').order_by('-end_date')[:3]

    # Get stats
    context['active_trip'] = active_trip
    context['upcoming_trips'] = upcoming_trips
    context['past_trips'] = past_trips
    context['total_trips'] = Trip.objects.filter(family__in=user_families).count()
    context['families_count'] = user_families.count()

    # Get resort for active trip if exists
    if active_trip:
        try:
            context['active_resort'] = active_trip.resort
        except:
            context['active_resort'] = None

    return render(request, 'core/dashboard.html', context)
