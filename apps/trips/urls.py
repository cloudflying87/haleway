"""
URL patterns for trips app.
"""

from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    # Trip list views
    path("", views.TripListView.as_view(), name="trip_list"),
    path("dream/", views.DreamTripsListView.as_view(), name="dream_trip_list"),
    path("resorts/", views.ResortsListView.as_view(), name="resort_list"),
    path("family/<uuid:family_pk>/", views.FamilyTripListView.as_view(), name="family_trip_list"),
    # Trip CRUD
    path("<uuid:pk>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("family/<uuid:family_pk>/create/", views.TripCreateView.as_view(), name="trip_create"),
    path("<uuid:pk>/edit/", views.TripUpdateView.as_view(), name="trip_edit"),
    path("<uuid:pk>/delete/", views.TripDeleteView.as_view(), name="trip_delete"),
    # Resort management
    path("<uuid:trip_pk>/resort/edit/", views.edit_resort, name="resort_edit"),
    # Weather forecast
    path("<uuid:pk>/weather/", views.trip_weather, name="trip_weather"),
]
