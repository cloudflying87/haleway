"""
Views for dream trips and resort wishlist functionality.
Separated from main views.py for better organization.
"""

import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.families.models import Family, FamilyMember

from .forms import ConvertDreamTripForm, ResortWishlistForm, TripResortOptionForm
from .models import Resort, ResortWishlist, Trip, TripResortOption

logger = structlog.get_logger(__name__)


# ============================================================================
# RESORT WISHLIST VIEWS
# ============================================================================


class ResortWishlistListView(LoginRequiredMixin, ListView):
    """List all resort wishlist items for user's families."""

    model = ResortWishlist
    template_name = "trips/wishlist/wishlist_list.html"
    context_object_name = "wishlist_items"
    paginate_by = 24

    def get_queryset(self):
        """Return wishlist items for families the user belongs to."""
        queryset = ResortWishlist.objects.filter(
            family__members__user=self.request.user
        ).select_related("family", "added_by", "visited_trip")

        # Filter by favorite
        if self.request.GET.get("favorites") == "true":
            queryset = queryset.filter(is_favorite=True)

        # Filter by visited
        visited_filter = self.request.GET.get("visited")
        if visited_filter == "yes":
            queryset = queryset.filter(visited=True)
        elif visited_filter == "no":
            queryset = queryset.filter(visited=False)

        # Filter by destination (search)
        destination_query = self.request.GET.get("destination")
        if destination_query:
            queryset = queryset.filter(destination__icontains=destination_query)

        # Filter by tags
        tag_query = self.request.GET.get("tag")
        if tag_query:
            queryset = queryset.filter(tags__icontains=tag_query)

        return queryset.order_by("-is_favorite", "destination", "name")

    def get_context_data(self, **kwargs):
        """Add filter context."""
        context = super().get_context_data(**kwargs)
        context["user_families"] = Family.objects.filter(members__user=self.request.user).distinct()

        # Get unique tags for filter
        all_wishlist = ResortWishlist.objects.filter(family__members__user=self.request.user)
        all_tags = set()
        for item in all_wishlist:
            all_tags.update(item.get_tags_list())
        context["all_tags"] = sorted(all_tags)

        # Pass current filters
        context["current_favorites"] = self.request.GET.get("favorites")
        context["current_visited"] = self.request.GET.get("visited")
        context["current_destination"] = self.request.GET.get("destination", "")
        context["current_tag"] = self.request.GET.get("tag")

        return context


class ResortWishlistDetailView(LoginRequiredMixin, DetailView):
    """Display wishlist item details."""

    model = ResortWishlist
    template_name = "trips/wishlist/wishlist_detail.html"
    context_object_name = "wishlist_item"

    def get_queryset(self):
        """Ensure user can only view wishlist from their families."""
        return ResortWishlist.objects.filter(
            family__members__user=self.request.user
        ).select_related("family", "added_by", "visited_trip")

    def get_context_data(self, **kwargs):
        """Add permissions context."""
        context = super().get_context_data(**kwargs)
        wishlist_item = self.object

        # Check if user can edit/delete
        try:
            membership = FamilyMember.objects.get(
                family=wishlist_item.family, user=self.request.user
            )
            context["can_edit"] = True
            context["can_delete"] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context["can_edit"] = False
            context["can_delete"] = False

        # Get dream trips for this family (for "Add to Dream Trip" feature)
        context["dream_trips"] = Trip.objects.filter(
            family=wishlist_item.family, status="dream"
        ).order_by("-created_at")

        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN

        return context


class ResortWishlistCreateView(LoginRequiredMixin, CreateView):
    """Create a new resort wishlist item."""

    model = ResortWishlist
    form_class = ResortWishlistForm
    template_name = "trips/wishlist/wishlist_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the family."""
        self.family = get_object_or_404(
            Family, pk=self.kwargs["family_pk"], members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add family context."""
        context = super().get_context_data(**kwargs)
        context["family"] = self.family
        context["page_title"] = f"Add Resort to {self.family.name}'s Wishlist"
        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN
        return context

    def form_valid(self, form):
        """Save the wishlist item."""
        wishlist_item = form.save(commit=False)
        wishlist_item.family = self.family
        wishlist_item.added_by = self.request.user
        wishlist_item.save()

        logger.info(
            "resort_wishlist_created",
            wishlist_id=str(wishlist_item.id),
            resort_name=wishlist_item.name,
            destination=wishlist_item.destination,
            family_id=str(self.family.id),
            user_id=self.request.user.id,
        )

        messages.success(self.request, _('"{}" added to wishlist!').format(wishlist_item.name))

        return redirect("trips:wishlist_detail", pk=wishlist_item.pk)


class ResortWishlistUpdateView(LoginRequiredMixin, UpdateView):
    """Update a resort wishlist item."""

    model = ResortWishlist
    form_class = ResortWishlistForm
    template_name = "trips/wishlist/wishlist_form.html"

    def get_queryset(self):
        """Ensure user can only edit wishlist from their families."""
        return ResortWishlist.objects.filter(family__members__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "resort_wishlist_updated",
            wishlist_id=str(self.object.id),
            resort_name=self.object.name,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Wishlist item updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to detail page."""
        return reverse_lazy("trips:wishlist_detail", kwargs={"pk": self.object.pk})


class ResortWishlistDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a resort wishlist item."""

    model = ResortWishlist
    template_name = "trips/wishlist/wishlist_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete wishlist items."""
        return ResortWishlist.objects.filter(
            family__members__user=self.request.user,
            family__members__role__in=["owner", "admin"],
        )

    def get_success_url(self):
        """Redirect to wishlist list."""
        return reverse_lazy("trips:wishlist_list")

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        wishlist_item = self.get_object()
        logger.info(
            "resort_wishlist_deleted",
            wishlist_id=str(wishlist_item.id),
            resort_name=wishlist_item.name,
            user_id=request.user.id,
        )
        messages.success(request, _("Wishlist item deleted successfully."))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# TRIP RESORT OPTION VIEWS (for Dream Trips)
# ============================================================================


class TripResortOptionListView(LoginRequiredMixin, DetailView):
    """Display all resort options for a dream trip with comparison view."""

    model = Trip
    template_name = "trips/dream_trips/resort_options_list.html"
    context_object_name = "trip"

    def get_queryset(self):
        """Ensure user can only view trips from their families."""
        return Trip.objects.filter(
            family__members__user=self.request.user, status="dream"
        ).select_related("family", "created_by")

    def get_context_data(self, **kwargs):
        """Add resort options."""
        context = super().get_context_data(**kwargs)
        trip = self.object

        # Get all resort options for this trip
        context["resort_options"] = TripResortOption.objects.filter(trip=trip).order_by(
            "-is_preferred", "order", "name"
        )

        # Check permissions
        try:
            membership = FamilyMember.objects.get(family=trip.family, user=self.request.user)
            context["can_edit"] = True
            context["can_delete"] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context["can_edit"] = False
            context["can_delete"] = False

        return context


class TripResortOptionCreateView(LoginRequiredMixin, CreateView):
    """Add a resort option to a dream trip."""

    model = TripResortOption
    form_class = TripResortOptionForm
    template_name = "trips/dream_trips/resort_option_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user can access this trip and it's a dream trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs["trip_pk"],
            family__members__user=request.user,
            status="dream",
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["page_title"] = f"Add Resort Option to {self.trip.name}"
        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN
        return context

    def form_valid(self, form):
        """Save the resort option."""
        resort_option = form.save(commit=False)
        resort_option.trip = self.trip

        # Auto-increment order
        max_order = TripResortOption.objects.filter(trip=self.trip).count()
        resort_option.order = max_order + 1
        resort_option.save()

        logger.info(
            "trip_resort_option_created",
            option_id=str(resort_option.id),
            resort_name=resort_option.name,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id,
        )

        messages.success(
            self.request,
            _('Resort option "{}" added to {}!').format(resort_option.name, self.trip.name),
        )

        return redirect("trips:resort_options_list", pk=self.trip.pk)


class TripResortOptionUpdateView(LoginRequiredMixin, UpdateView):
    """Update a resort option."""

    model = TripResortOption
    form_class = TripResortOptionForm
    template_name = "trips/dream_trips/resort_option_form.html"

    def get_queryset(self):
        """Ensure user can only edit options from their trips."""
        return TripResortOption.objects.filter(
            trip__family__members__user=self.request.user
        ).select_related("trip")

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.object.trip
        context["page_title"] = f"Edit {self.object.name}"
        context["mapbox_token"] = settings.MAPBOX_ACCESS_TOKEN
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "trip_resort_option_updated",
            option_id=str(self.object.id),
            resort_name=self.object.name,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Resort option updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to resort options list."""
        return reverse_lazy("trips:resort_options_list", kwargs={"pk": self.object.trip.pk})


class TripResortOptionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a resort option."""

    model = TripResortOption
    template_name = "trips/dream_trips/resort_option_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete options."""
        return TripResortOption.objects.filter(
            trip__family__members__user=self.request.user,
            trip__family__members__role__in=["owner", "admin"],
        ).select_related("trip")

    def get_success_url(self):
        """Redirect to resort options list."""
        return reverse_lazy("trips:resort_options_list", kwargs={"pk": self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        option = self.get_object()
        logger.info(
            "trip_resort_option_deleted",
            option_id=str(option.id),
            resort_name=option.name,
            user_id=request.user.id,
        )
        messages.success(request, _("Resort option deleted successfully."))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# DREAM TRIP CONVERSION VIEW
# ============================================================================


class ConvertDreamTripView(LoginRequiredMixin, UpdateView):
    """Convert a dream trip to a planning trip."""

    model = Trip
    form_class = ConvertDreamTripForm
    template_name = "trips/dream_trips/convert_to_planning.html"

    def get_queryset(self):
        """Ensure user can only convert trips from their families and it's a dream trip."""
        return Trip.objects.filter(
            family__members__user=self.request.user, status="dream"
        ).select_related("family")

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        trip = self.object

        # Get all resort options for this trip
        context["resort_options"] = TripResortOption.objects.filter(trip=trip).order_by(
            "-is_preferred", "order"
        )

        return context

    def form_valid(self, form):
        """Convert the trip."""
        trip = self.object
        chosen_option = form.cleaned_data.get("chosen_resort_option")

        with transaction.atomic():
            # Update trip status and dates
            trip.status = "planning"
            trip.start_date = form.cleaned_data["start_date"]
            trip.end_date = form.cleaned_data["end_date"]
            trip.save()

            # If a resort option was chosen, convert it to the main resort
            if chosen_option:
                # Delete existing resort if any
                try:
                    existing_resort = trip.resort
                    existing_resort.delete()
                except Resort.DoesNotExist:
                    pass

                # Create new resort from chosen option
                Resort.objects.create(
                    trip=trip,
                    name=chosen_option.name,
                    website_url=chosen_option.website_url,
                    phone_number=chosen_option.phone_number,
                    address_line1=chosen_option.address_line1,
                    address_line2=chosen_option.address_line2,
                    city=chosen_option.city,
                    state=chosen_option.state,
                    zip_code=chosen_option.zip_code,
                    country=chosen_option.country,
                    latitude=chosen_option.latitude,
                    longitude=chosen_option.longitude,
                    general_notes=chosen_option.general_notes,
                )

                logger.info(
                    "dream_trip_converted",
                    trip_id=str(trip.id),
                    trip_name=trip.name,
                    chosen_resort=chosen_option.name,
                    user_id=self.request.user.id,
                )
            else:
                logger.info(
                    "dream_trip_converted_no_resort",
                    trip_id=str(trip.id),
                    trip_name=trip.name,
                    user_id=self.request.user.id,
                )

        messages.success(
            self.request,
            _(
                'Dream trip "{}" converted to planning trip! You can now add itinerary, packing lists, and more.'
            ).format(trip.name),
        )

        return redirect("trips:trip_detail", pk=trip.pk)
