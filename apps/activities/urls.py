"""
URL configuration for activities app.
"""
from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # Activity list for a trip
    path('trip/<uuid:trip_pk>/', views.TripActivityListView.as_view(), name='activity_list'),

    # Activity CRUD
    path('trip/<uuid:trip_pk>/create/', views.ActivityCreateView.as_view(), name='activity_create'),
    path('<uuid:pk>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('<uuid:pk>/edit/', views.ActivityUpdateView.as_view(), name='activity_edit'),
    path('<uuid:pk>/delete/', views.ActivityDeleteView.as_view(), name='activity_delete'),

    # Rating
    path('<uuid:pk>/rate/', views.rate_activity, name='activity_rate'),

    # Priority update (AJAX)
    path('update-priority/', views.update_priority, name='update_priority'),
]
