"""
URL configuration for budget app.
"""
from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    # Budget Overview
    path('<uuid:trip_pk>/', views.TripBudgetView.as_view(), name='budget_overview'),

    # Budget Category URLs
    path('<uuid:trip_pk>/category/create/', views.BudgetCategoryCreateView.as_view(), name='category_create'),
    path('category/<uuid:pk>/edit/', views.BudgetCategoryUpdateView.as_view(), name='category_update'),
    path('category/<uuid:pk>/delete/', views.BudgetCategoryDeleteView.as_view(), name='category_delete'),

    # Budget Item URLs
    path('<uuid:trip_pk>/item/create/', views.BudgetItemCreateView.as_view(), name='item_create'),
    path('item/<uuid:pk>/edit/', views.BudgetItemUpdateView.as_view(), name='item_update'),
    path('item/<uuid:pk>/delete/', views.BudgetItemDeleteView.as_view(), name='item_delete'),

    # Add from Activity
    path('add-from-activity/<uuid:activity_pk>/', views.add_activity_to_budget, name='add_from_activity'),
]
