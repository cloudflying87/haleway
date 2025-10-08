"""
Views for trip memories: photos and journal entries.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.translation import gettext_lazy as _
import structlog

from apps.families.models import Family
from apps.trips.models import Trip
from .models import TripPhoto, DailyJournal
from .forms import TripPhotoForm, QuickPhotoUploadForm, DailyJournalForm

logger = structlog.get_logger(__name__)


# ============================================================================
# Photo Views
# ============================================================================

class TripPhotoListView(LoginRequiredMixin, ListView):
    """Gallery view of all photos for a trip."""
    model = TripPhoto
    template_name = 'memories/photo_gallery.html'
    context_object_name = 'photos'
    paginate_by = 24  # Show 24 photos per page (4x6 grid)

    def get_queryset(self):
        """Return photos for the specified trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )
        return TripPhoto.objects.filter(trip=self.trip).select_related(
            'uploaded_by', 'activity', 'daily_itinerary'
        ).order_by('-taken_date', '-uploaded_at')

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        return context


class TripPhotoDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single photo."""
    model = TripPhoto
    template_name = 'memories/photo_detail.html'
    context_object_name = 'photo'

    def get_queryset(self):
        """Ensure user can only view photos from their trips."""
        return TripPhoto.objects.filter(
            trip__family__members__user=self.request.user
        ).select_related('trip', 'uploaded_by', 'activity', 'daily_itinerary')


class TripPhotoCreateView(LoginRequiredMixin, CreateView):
    """Upload a new photo."""
    model = TripPhoto
    form_class = TripPhotoForm
    template_name = 'memories/photo_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the trip's family."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'Upload Photo to {self.trip.name}'
        return context

    def form_valid(self, form):
        """Set trip and uploaded_by."""
        form.instance.trip = self.trip
        form.instance.uploaded_by = self.request.user

        logger.info(
            "photo_uploaded",
            trip_id=str(self.trip.id),
            trip_name=self.trip.name,
            user_id=self.request.user.id
        )

        messages.success(self.request, _('Photo uploaded successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to photo gallery."""
        return reverse_lazy('memories:photo_gallery', kwargs={'trip_pk': self.trip.pk})


class TripPhotoUpdateView(LoginRequiredMixin, UpdateView):
    """Edit photo details (caption, date, links)."""
    model = TripPhoto
    form_class = TripPhotoForm
    template_name = 'memories/photo_form.html'

    def get_queryset(self):
        """Ensure user can only edit photos they uploaded."""
        return TripPhoto.objects.filter(
            trip__family__members__user=self.request.user,
            uploaded_by=self.request.user
        )

    def get_form_kwargs(self):
        """Pass trip to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.object.trip
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit Photo'
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "photo_updated",
            photo_id=str(self.object.id),
            trip_id=str(self.object.trip.id),
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Photo updated successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to photo detail."""
        return reverse_lazy('memories:photo_detail', kwargs={'pk': self.object.pk})


class TripPhotoDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a photo."""
    model = TripPhoto
    template_name = 'memories/photo_confirm_delete.html'

    def get_queryset(self):
        """Ensure user can only delete photos they uploaded."""
        return TripPhoto.objects.filter(
            trip__family__members__user=self.request.user,
            uploaded_by=self.request.user
        )

    def get_success_url(self):
        """Redirect to photo gallery."""
        return reverse_lazy('memories:photo_gallery', kwargs={'trip_pk': self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        photo = self.get_object()
        logger.info(
            "photo_deleted",
            photo_id=str(photo.id),
            trip_id=str(photo.trip.id),
            user_id=request.user.id
        )
        messages.success(request, _('Photo deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Journal Views
# ============================================================================

class TripJournalListView(LoginRequiredMixin, ListView):
    """List all journal entries for a trip."""
    model = DailyJournal
    template_name = 'memories/journal_list.html'
    context_object_name = 'journal_entries'

    def get_queryset(self):
        """Return journal entries for the specified trip."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=self.request.user
        )
        return DailyJournal.objects.filter(trip=self.trip).select_related(
            'created_by'
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        return context


class DailyJournalDetailView(LoginRequiredMixin, DetailView):
    """View a journal entry."""
    model = DailyJournal
    template_name = 'memories/journal_detail.html'
    context_object_name = 'journal'

    def get_queryset(self):
        """Ensure user can only view journals from their trips."""
        return DailyJournal.objects.filter(
            trip__family__members__user=self.request.user
        ).select_related('trip', 'created_by')


class DailyJournalCreateView(LoginRequiredMixin, CreateView):
    """Create a new journal entry."""
    model = DailyJournal
    form_class = DailyJournalForm
    template_name = 'memories/journal_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Verify user is a member of the trip's family."""
        self.trip = get_object_or_404(
            Trip,
            pk=self.kwargs['trip_pk'],
            family__members__user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pass trip and user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.trip
        kwargs['created_by'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add trip context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.trip
        context['page_title'] = f'New Journal Entry for {self.trip.name}'
        return context

    def form_valid(self, form):
        """Set trip and created_by."""
        form.instance.trip = self.trip
        form.instance.created_by = self.request.user

        logger.info(
            "journal_created",
            trip_id=str(self.trip.id),
            trip_name=self.trip.name,
            date=str(form.instance.date),
            user_id=self.request.user.id
        )

        messages.success(self.request, _('Journal entry created successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to journal list."""
        return reverse_lazy('memories:journal_list', kwargs={'trip_pk': self.trip.pk})


class DailyJournalUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a journal entry."""
    model = DailyJournal
    form_class = DailyJournalForm
    template_name = 'memories/journal_form.html'

    def get_queryset(self):
        """Ensure user can only edit journals they created."""
        return DailyJournal.objects.filter(
            trip__family__members__user=self.request.user,
            created_by=self.request.user
        )

    def get_form_kwargs(self):
        """Pass trip and user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trip'] = self.object.trip
        kwargs['created_by'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['trip'] = self.object.trip
        context['page_title'] = f'Edit Journal Entry'
        return context

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "journal_updated",
            journal_id=str(self.object.id),
            trip_id=str(self.object.trip.id),
            user_id=self.request.user.id
        )
        messages.success(self.request, _('Journal entry updated successfully!'))
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to journal detail."""
        return reverse_lazy('memories:journal_detail', kwargs={'pk': self.object.pk})


class DailyJournalDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a journal entry."""
    model = DailyJournal
    template_name = 'memories/journal_confirm_delete.html'

    def get_queryset(self):
        """Ensure user can only delete journals they created."""
        return DailyJournal.objects.filter(
            trip__family__members__user=self.request.user,
            created_by=self.request.user
        )

    def get_success_url(self):
        """Redirect to journal list."""
        return reverse_lazy('memories:journal_list', kwargs={'trip_pk': self.object.trip.pk})

    def delete(self, request, *args, **kwargs):
        """Log the deletion."""
        journal = self.get_object()
        logger.info(
            "journal_deleted",
            journal_id=str(journal.id),
            trip_id=str(journal.trip.id),
            user_id=request.user.id
        )
        messages.success(request, _('Journal entry deleted successfully.'))
        return super().delete(request, *args, **kwargs)
