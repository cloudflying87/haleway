"""
Core app URL configuration.
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", login_required(views.dashboard), name="dashboard"),
    path("api/trips/", views.get_user_trips, name="get_user_trips"),
    path("api/trips/set-current/", views.set_current_trip, name="set_current_trip"),
]
