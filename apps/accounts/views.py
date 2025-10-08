"""
Authentication views for web interface.
"""

import structlog
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserProfileForm, UserRegistrationForm

logger = structlog.get_logger(__name__)


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to HaleWay!")
            return redirect("core:dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    """User profile view and edit."""
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            logger.info("profile_updated", user_id=request.user.id, username=request.user.username)
            messages.success(request, "Profile updated successfully!")
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
        },
    )


def logout_view(request):
    """Custom logout view that immediately logs out the user."""
    # Log the logout
    logger.info(
        "user_logout",
        user_id=request.user.id if request.user.is_authenticated else None,
        username=request.user.username if request.user.is_authenticated else None,
    )
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")
