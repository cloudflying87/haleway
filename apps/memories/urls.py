"""
URL configuration for memories app.
"""
from django.urls import path
from . import views

app_name = 'memories'

urlpatterns = [
    # Photo URLs
    path('trip/<uuid:trip_pk>/photos/', views.TripPhotoListView.as_view(), name='photo_gallery'),
    path('trip/<uuid:trip_pk>/photos/upload/', views.TripPhotoCreateView.as_view(), name='photo_upload'),
    path('photos/<uuid:pk>/', views.TripPhotoDetailView.as_view(), name='photo_detail'),
    path('photos/<uuid:pk>/edit/', views.TripPhotoUpdateView.as_view(), name='photo_edit'),
    path('photos/<uuid:pk>/delete/', views.TripPhotoDeleteView.as_view(), name='photo_delete'),

    # Journal URLs
    path('trip/<uuid:trip_pk>/journal/', views.TripJournalListView.as_view(), name='journal_list'),
    path('trip/<uuid:trip_pk>/journal/new/', views.DailyJournalCreateView.as_view(), name='journal_create'),
    path('journal/<uuid:pk>/', views.DailyJournalDetailView.as_view(), name='journal_detail'),
    path('journal/<uuid:pk>/edit/', views.DailyJournalUpdateView.as_view(), name='journal_edit'),
    path('journal/<uuid:pk>/delete/', views.DailyJournalDeleteView.as_view(), name='journal_delete'),
]
