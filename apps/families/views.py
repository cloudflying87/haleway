"""
Views for family management.
"""

import structlog
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import FamilyForm, FamilyInvitationForm
from .models import Family, FamilyInvitation, FamilyMember

logger = structlog.get_logger(__name__)


class FamilyListView(LoginRequiredMixin, ListView):
    """List all families the user is a member of."""

    model = Family
    template_name = "families/family_list.html"
    context_object_name = "families"

    def get_queryset(self):
        """Return only families the user is a member of."""
        return (
            Family.objects.filter(members__user=self.request.user)
            .distinct()
            .order_by("-created_at")
        )


class FamilyDetailView(LoginRequiredMixin, DetailView):
    """Display family details and members."""

    model = Family
    template_name = "families/family_detail.html"
    context_object_name = "family"

    def get_queryset(self):
        """Ensure user can only view families they're a member of."""
        return Family.objects.filter(members__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add additional context."""
        context = super().get_context_data(**kwargs)
        family = self.object

        # Get the current user's membership
        try:
            membership = FamilyMember.objects.get(family=family, user=self.request.user)
            context["user_membership"] = membership
            context["can_invite"] = membership.can_invite_members()
            context["can_manage"] = membership.can_manage_members()
        except FamilyMember.DoesNotExist:
            context["user_membership"] = None
            context["can_invite"] = False
            context["can_manage"] = False

        # Get all members and pending invitations
        context["members"] = family.get_all_members()
        context["pending_invitations"] = family.invitations.filter(status="pending").order_by(
            "-created_at"
        )

        # Add invitation form if user can invite
        if context["can_invite"]:
            context["invitation_form"] = FamilyInvitationForm(
                family=family, invited_by=self.request.user
            )

        return context


class FamilyCreateView(LoginRequiredMixin, CreateView):
    """Create a new family."""

    model = Family
    form_class = FamilyForm
    template_name = "families/family_form.html"
    success_url = reverse_lazy("families:family_list")

    def form_valid(self, form):
        """Save the family and create the owner membership."""
        with transaction.atomic():
            # Save the family
            self.object = form.save()

            # Create the owner membership
            FamilyMember.objects.create(family=self.object, user=self.request.user, role="owner")

            logger.info(
                "family_created",
                family_id=str(self.object.id),
                family_name=self.object.name,
                user_id=self.request.user.id,
            )

            messages.success(
                self.request, _('Family "{}" created successfully!').format(self.object.name)
            )

        return super().form_valid(form)


class FamilyUpdateView(LoginRequiredMixin, UpdateView):
    """Update family details."""

    model = Family
    form_class = FamilyForm
    template_name = "families/family_form.html"

    def get_queryset(self):
        """Ensure only admins can edit."""
        return Family.objects.filter(
            members__user=self.request.user, members__role__in=["owner", "admin"]
        )

    def get_success_url(self):
        """Redirect to family detail page."""
        return reverse_lazy("families:family_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        """Log the update."""
        logger.info(
            "family_updated",
            family_id=str(self.object.id),
            family_name=self.object.name,
            user_id=self.request.user.id,
        )
        messages.success(self.request, _("Family updated successfully!"))
        return super().form_valid(form)


@login_required
def invite_member(request, pk):
    """Invite a new member to the family."""
    family = get_object_or_404(
        Family, pk=pk, members__user=request.user, members__role__in=["owner", "admin"]
    )

    if request.method == "POST":
        form = FamilyInvitationForm(request.POST, family=family, invited_by=request.user)

        if form.is_valid():
            invitation = form.save()
            logger.info(
                "invitation_sent",
                invitation_id=str(invitation.id),
                family_id=str(family.id),
                email=invitation.email,
                invited_by_id=request.user.id,
            )
            messages.success(request, _("Invitation sent to {}!").format(invitation.email))
            return redirect("families:family_detail", pk=family.pk)
        else:
            messages.error(request, _("Failed to send invitation. Please check the form."))

    return redirect("families:family_detail", pk=family.pk)


@login_required
def accept_invitation(request, token):
    """Accept a family invitation."""
    invitation = get_object_or_404(FamilyInvitation, token=token, email=request.user.email)

    if not invitation.is_valid():
        messages.error(request, _("This invitation has expired or is no longer valid."))
        return redirect("families:family_list")

    # Check if user is already a member
    if FamilyMember.objects.filter(family=invitation.family, user=request.user).exists():
        messages.info(request, _("You are already a member of this family."))
        invitation.mark_accepted()
        return redirect("families:family_detail", pk=invitation.family.pk)

    with transaction.atomic():
        # Create the membership
        FamilyMember.objects.create(family=invitation.family, user=request.user, role="member")

        # Mark invitation as accepted
        invitation.mark_accepted()

        logger.info(
            "invitation_accepted",
            invitation_id=str(invitation.id),
            family_id=str(invitation.family.id),
            user_id=request.user.id,
        )

        messages.success(request, _("Welcome to {}!").format(invitation.family.name))

    return redirect("families:family_detail", pk=invitation.family.pk)


@login_required
def cancel_invitation(request, pk):
    """Cancel a pending invitation."""
    invitation = get_object_or_404(
        FamilyInvitation,
        pk=pk,
        family__members__user=request.user,
        family__members__role__in=["owner", "admin"],
    )

    if request.method == "POST":
        family_id = invitation.family.pk
        invitation.mark_expired()

        logger.info(
            "invitation_cancelled",
            invitation_id=str(invitation.id),
            family_id=str(family_id),
            cancelled_by_id=request.user.id,
        )

        messages.success(request, _("Invitation cancelled."))
        return redirect("families:family_detail", pk=family_id)

    return redirect("families:family_detail", pk=invitation.family.pk)


@login_required
def remove_member(request, family_pk, member_pk):
    """Remove a member from the family."""
    family = get_object_or_404(Family, pk=family_pk)

    # Check if requester is an admin
    requester_membership = get_object_or_404(
        FamilyMember, family=family, user=request.user, role__in=["owner", "admin"]
    )

    # Get the member to remove
    member = get_object_or_404(FamilyMember, pk=member_pk, family=family)

    # Don't allow removing the owner
    if member.is_owner():
        messages.error(request, _("Cannot remove the family owner."))
        return redirect("families:family_detail", pk=family.pk)

    # Don't allow non-owners to remove admins
    if member.is_admin() and not requester_membership.is_owner():
        messages.error(request, _("Only the family owner can remove administrators."))
        return redirect("families:family_detail", pk=family.pk)

    if request.method == "POST":
        user_name = member.user.get_full_name()
        member.delete()

        logger.info(
            "member_removed",
            family_id=str(family.id),
            removed_user_id=member.user.id,
            removed_by_id=request.user.id,
        )

        messages.success(request, _("Removed {} from the family.").format(user_name))
        return redirect("families:family_detail", pk=family.pk)

    return redirect("families:family_detail", pk=family.pk)
