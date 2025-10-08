"""
URL patterns for notes app.
"""
from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # Note list and search
    path('trip/<uuid:trip_pk>/', views.TripNoteListView.as_view(), name='note_list'),

    # Note CRUD
    path('<uuid:pk>/', views.NoteDetailView.as_view(), name='note_detail'),
    path('trip/<uuid:trip_pk>/create/', views.NoteCreateView.as_view(), name='note_create'),
    path('<uuid:pk>/edit/', views.NoteUpdateView.as_view(), name='note_edit'),
    path('<uuid:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),

    # Category management
    path('trip/<uuid:trip_pk>/category/create/', views.NoteCategoryCreateView.as_view(), name='category_create'),
    path('category/<uuid:pk>/edit/', views.NoteCategoryUpdateView.as_view(), name='category_update'),
    path('category/<uuid:pk>/delete/', views.NoteCategoryDeleteView.as_view(), name='category_delete'),
]
