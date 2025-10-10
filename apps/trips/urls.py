"""
URL patterns for trips app.
"""

from django.urls import path

from . import views, views_dream_trips

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
    # Resort Wishlist
    path("wishlist/", views_dream_trips.ResortWishlistListView.as_view(), name="wishlist_list"),
    path(
        "wishlist/<uuid:pk>/",
        views_dream_trips.ResortWishlistDetailView.as_view(),
        name="wishlist_detail",
    ),
    path(
        "wishlist/family/<uuid:family_pk>/create/",
        views_dream_trips.ResortWishlistCreateView.as_view(),
        name="wishlist_create",
    ),
    path(
        "wishlist/<uuid:pk>/edit/",
        views_dream_trips.ResortWishlistUpdateView.as_view(),
        name="wishlist_edit",
    ),
    path(
        "wishlist/<uuid:pk>/delete/",
        views_dream_trips.ResortWishlistDeleteView.as_view(),
        name="wishlist_delete",
    ),
    # Trip Resort Options (for Dream Trips)
    path(
        "<uuid:pk>/resort-options/",
        views_dream_trips.TripResortOptionListView.as_view(),
        name="resort_options_list",
    ),
    path(
        "<uuid:trip_pk>/resort-options/add/",
        views_dream_trips.TripResortOptionCreateView.as_view(),
        name="resort_option_create",
    ),
    path(
        "resort-options/<uuid:pk>/edit/",
        views_dream_trips.TripResortOptionUpdateView.as_view(),
        name="resort_option_edit",
    ),
    path(
        "resort-options/<uuid:pk>/delete/",
        views_dream_trips.TripResortOptionDeleteView.as_view(),
        name="resort_option_delete",
    ),
    # Convert Dream Trip to Planning
    path(
        "<uuid:pk>/convert-to-planning/",
        views_dream_trips.ConvertDreamTripView.as_view(),
        name="convert_dream_trip",
    ),
]
