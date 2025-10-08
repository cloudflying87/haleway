"""
URL patterns for families app.
"""
from django.urls import path
from . import views

app_name = 'families'

urlpatterns = [
    # Family management
    path('', views.FamilyListView.as_view(), name='family_list'),
    path('create/', views.FamilyCreateView.as_view(), name='family_create'),
    path('<uuid:pk>/', views.FamilyDetailView.as_view(), name='family_detail'),
    path('<uuid:pk>/edit/', views.FamilyUpdateView.as_view(), name='family_edit'),

    # Member invitations
    path('<uuid:pk>/invite/', views.invite_member, name='invite_member'),
    path('invitation/<uuid:pk>/cancel/', views.cancel_invitation, name='cancel_invitation'),
    path('invitation/<str:token>/accept/', views.accept_invitation, name='accept_invitation'),

    # Member management
    path('<uuid:family_pk>/member/<uuid:member_pk>/remove/', views.remove_member, name='remove_member'),
]
