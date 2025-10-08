"""
URL configuration for itinerary app.
"""

from django.urls import path

from . import views

app_name = "itinerary"

urlpatterns = [
    # Calendar view for entire trip
    path("trip/<uuid:trip_pk>/calendar/", views.TripCalendarView.as_view(), name="calendar"),
    # Day detail view
    path("trip/<uuid:trip_pk>/day/<str:date>/", views.DayDetailView.as_view(), name="day_detail"),
    # Itinerary item CRUD
    path("trip/<uuid:trip_pk>/add/", views.ItineraryItemCreateView.as_view(), name="item_create"),
    path("item/<uuid:pk>/edit/", views.ItineraryItemUpdateView.as_view(), name="item_edit"),
    path("item/<uuid:pk>/delete/", views.ItineraryItemDeleteView.as_view(), name="item_delete"),
    # Quick-add event
    path("trip/<uuid:trip_pk>/quick-add/", views.quick_add_event, name="quick_add_event"),
    path(
        "trip/<uuid:trip_pk>/quick-add/<str:date_str>/",
        views.quick_add_event,
        name="quick_add_event_date",
    ),
    # Assign activity to day
    path(
        "trip/<uuid:trip_pk>/assign-activity/<uuid:activity_pk>/",
        views.assign_activity,
        name="assign_activity",
    ),
]
