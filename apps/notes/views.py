"""
Views for note and category management.
"""

import structlog
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .forms import NoteCategoryForm, NoteForm, NoteSearchForm
from .models import Note, NoteCategory

logger = structlog.get_logger(__name__)


class TripNoteListView(LoginRequiredMixin, ListView):
    """List all notes for a trip with search functionality."""

    model = Note
    template_name = "notes/note_list.html"
    context_object_name = "notes"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        """Verify user has access to this trip."""
        user_families = Family.objects.filter(members__user=request.user)
        self.trip = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], family__in=user_families)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Return notes for the trip, with optional search and filtering."""
        queryset = Note.objects.filter(trip=self.trip).select_related("category", "created_by")

        # Get search parameters
        self.search_form = NoteSearchForm(self.request.GET, trip=self.trip)

        if self.search_form.is_valid():
            query = self.search_form.cleaned_data.get("query")
            category = self.search_form.cleaned_data.get("category")
            pinned_only = self.search_form.cleaned_data.get("pinned_only")

            # Full-text search on title and content
            if query:
                search_query = SearchQuery(query)
                queryset = (
                    queryset.annotate(
                        search=SearchVector("title", "content"),
                        rank=SearchRank(SearchVector("title", "content"), search_query),
                    )
                    .filter(search=search_query)
                    .order_by("-rank", "-is_pinned", "-updated_at")
                )

                logger.info(
                    "note_search_performed",
                    trip_id=str(self.trip.id),
                    query=query,
                    result_count=queryset.count(),
                    user_id=self.request.user.id,
                )

            # Filter by category
            if category:
                queryset = queryset.filter(category=category)

            # Filter by pinned
            if pinned_only:
                queryset = queryset.filter(is_pinned=True)

        return queryset

    def get_context_data(self, **kwargs):
        """Add trip and form context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["search_form"] = self.search_form
        context["categories"] = NoteCategory.objects.filter(trip=self.trip)

        # Check if user can create notes
        try:
            membership = FamilyMember.objects.get(family=self.trip.family, user=self.request.user)
            context["can_create_note"] = True  # All members can create notes
            context["can_manage_categories"] = membership.is_admin()
        except FamilyMember.DoesNotExist:
            context["can_create_note"] = False
            context["can_manage_categories"] = False

        return context


class NoteDetailView(LoginRequiredMixin, DetailView):
    """Display note details."""

    model = Note
    template_name = "notes/note_detail.html"
    context_object_name = "note"

    def get_queryset(self):
        """Ensure user can only view notes from their trips."""
        user_families = Family.objects.filter(members__user=self.request.user)
        return Note.objects.filter(trip__family__in=user_families).select_related(
            "trip", "category", "created_by"
        )

    def get_context_data(self, **kwargs):
        """Add permissions context."""
        context = super().get_context_data(**kwargs)
        note = self.object

        # Check if user can edit/delete
        try:
            membership = FamilyMember.objects.get(family=note.trip.family, user=self.request.user)
            # Admins and note creator can edit
            context["can_edit"] = membership.is_admin() or note.created_by == self.request.user
            context["can_delete"] = membership.is_admin() or note.created_by == self.request.user
        except FamilyMember.DoesNotExist:
            context["can_edit"] = False
            context["can_delete"] = False

        return context


class NoteCreateView(LoginRequiredMixin, CreateView):
    """Create a new note for a trip."""

    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the trip's family."""
        user_families = Family.objects.filter(members__user=request.user)
        self.trip = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], family__in=user_families)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip and user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.trip
        kwargs["created_by"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["page_title"] = f"Create Note for {self.trip.name}"
        return context

    def form_valid(self, form):
        """Log the creation."""
        response = super().form_valid(form)
        messages.success(
            self.request, _('Note "{}" created successfully!').format(self.object.title)
        )
        return response

    def get_success_url(self):
        """Redirect to next URL if provided, otherwise to trip's note list."""
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("notes:note_list", kwargs={"trip_pk": self.trip.pk})


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    """Update note details."""

    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"

    def get_queryset(self):
        """Ensure user can only edit notes they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        qs = Note.objects.filter(trip__family__in=user_families)

        # Non-admins can only edit their own notes
        try:
            # If we can get the note, check permissions
            note = qs.get(pk=self.kwargs["pk"])
            membership = FamilyMember.objects.get(family=note.trip.family, user=self.request.user)
            if not membership.is_admin() and note.created_by != self.request.user:
                return Note.objects.none()
        except (Note.DoesNotExist, FamilyMember.DoesNotExist):
            return Note.objects.none()

        return qs

    def get_form_kwargs(self):
        """Pass trip and user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.object.trip
        kwargs["created_by"] = self.object.created_by
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.object.trip
        context["page_title"] = f"Edit {self.object.title}"
        return context

    def form_valid(self, form):
        """Log the update."""
        messages.success(self.request, _("Note updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to next URL if provided, otherwise to note detail."""
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return self.object.get_absolute_url()


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a note."""

    model = Note
    template_name = "notes/note_confirm_delete.html"

    def get_queryset(self):
        """Ensure user can only delete notes they have permission for."""
        user_families = Family.objects.filter(members__user=self.request.user)
        qs = Note.objects.filter(trip__family__in=user_families)

        # Non-admins can only delete their own notes
        try:
            note = qs.get(pk=self.kwargs["pk"])
            membership = FamilyMember.objects.get(family=note.trip.family, user=self.request.user)
            if not membership.is_admin() and note.created_by != self.request.user:
                return Note.objects.none()
        except (Note.DoesNotExist, FamilyMember.DoesNotExist):
            return Note.objects.none()

        return qs

    def get_success_url(self):
        """Redirect to trip's note list."""
        return reverse_lazy("notes:note_list", kwargs={"trip_pk": self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        note = self.get_object()
        logger.info(
            "note_deleted",
            note_id=str(note.id),
            note_title=note.title,
            trip_id=str(note.trip.id),
            user_id=request.user.id,
        )
        messages.success(request, _("Note deleted successfully."))
        return super().delete(request, *args, **kwargs)


# Category Management Views


class NoteCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new note category for a trip."""

    model = NoteCategory
    form_class = NoteCategoryForm
    template_name = "notes/category_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Verify user is an admin of the trip's family."""
        admin_families = Family.objects.filter(
            members__user=request.user, members__role__in=["owner", "admin"]
        )
        self.trip = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], family__in=admin_families)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["page_title"] = f"Create Category for {self.trip.name}"
        return context

    def form_valid(self, form):
        """Log the creation."""
        response = super().form_valid(form)
        logger.info(
            "note_category_created",
            category_id=str(self.object.id),
            category_name=self.object.name,
            trip_id=str(self.trip.id),
            user_id=self.request.user.id,
        )
        messages.success(
            self.request, _('Category "{}" created successfully!').format(self.object.name)
        )
        return response

    def get_success_url(self):
        """Redirect to trip's note list."""
        return reverse_lazy("notes:note_list", kwargs={"trip_pk": self.trip.pk})


class NoteCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update note category details."""

    model = NoteCategory
    form_class = NoteCategoryForm
    template_name = "notes/category_form.html"

    def get_queryset(self):
        """Ensure only admins can update categories."""
        admin_families = Family.objects.filter(
            members__user=self.request.user, members__role__in=["owner", "admin"]
        )
        return NoteCategory.objects.filter(trip__family__in=admin_families)

    def get_form_kwargs(self):
        """Pass trip to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["trip"] = self.object.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context["trip"] = self.object.trip
        context["page_title"] = f"Edit Category: {self.object.name}"
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "note_category_updated",
            category_id=str(self.object.id),
            category_name=self.object.name,
            trip_id=str(self.object.trip.id),
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Category updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to trip's note list."""
        return reverse_lazy("notes:note_list", kwargs={"trip_pk": self.object.trip.pk})


class NoteCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a note category."""

    model = NoteCategory
    template_name = "notes/category_confirm_delete.html"

    def get_queryset(self):
        """Ensure only admins can delete categories."""
        admin_families = Family.objects.filter(
            members__user=self.request.user, members__role__in=["owner", "admin"]
        )
        return NoteCategory.objects.filter(trip__family__in=admin_families)

    def get_success_url(self):
        """Redirect to trip's note list."""
        return reverse_lazy("notes:note_list", kwargs={"trip_pk": self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        category = self.get_object()
        note_count = category.notes.count()
        logger.info(
            "note_category_deleted",
            category_id=str(category.id),
            category_name=category.name,
            trip_id=str(category.trip.id),
            notes_affected=note_count,
            user_id=request.user.id,
        )
        messages.success(
            request,
            _("Category deleted successfully. {} notes were uncategorized.").format(note_count),
        )
        return super().delete(request, *args, **kwargs)
