"""
Family management models for HaleWay.
Handles family creation, member management, and invitations.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import structlog

logger = structlog.get_logger(__name__)


class Family(models.Model):
    """
    Represents a family group that can share trips and memories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('family name'), max_length=200)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('family')
        verbose_name_plural = _('families')
        db_table = 'families'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_owner(self):
        """Return the family owner."""
        try:
            return self.members.get(role='owner').user
        except FamilyMember.DoesNotExist:
            logger.warning("family_has_no_owner", family_id=str(self.id), family_name=self.name)
            return None

    def get_admins(self):
        """Return all family admins (including owner)."""
        return self.members.filter(role__in=['owner', 'admin']).select_related('user')

    def get_all_members(self):
        """Return all family members."""
        return self.members.select_related('user').order_by('-joined_at')

    def member_count(self):
        """Return the number of members in the family."""
        return self.members.count()


class FamilyMember(models.Model):
    """
    Represents a user's membership in a family.
    """
    ROLE_CHOICES = [
        ('owner', _('Owner')),
        ('admin', _('Admin')),
        ('member', _('Member')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('family')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_memberships',
        verbose_name=_('user')
    )
    role = models.CharField(
        _('role'),
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)

    class Meta:
        verbose_name = _('family member')
        verbose_name_plural = _('family members')
        db_table = 'family_members'
        unique_together = [['family', 'user']]
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['family', 'role']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.family.name} ({self.get_role_display()})"

    def is_owner(self):
        """Check if this member is the family owner."""
        return self.role == 'owner'

    def is_admin(self):
        """Check if this member is an admin or owner."""
        return self.role in ['owner', 'admin']

    def can_manage_members(self):
        """Check if this member can manage other members."""
        return self.is_admin()

    def can_invite_members(self):
        """Check if this member can invite new members."""
        return self.is_admin()


class FamilyInvitation(models.Model):
    """
    Represents an invitation to join a family.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('expired', _('Expired')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('family')
    )
    email = models.EmailField(_('email address'))
    token = models.CharField(
        _('invitation token'),
        max_length=100,
        unique=True,
        default=uuid.uuid4
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name=_('invited by')
    )
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))

    class Meta:
        verbose_name = _('family invitation')
        verbose_name_plural = _('family invitations')
        db_table = 'family_invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['family', 'status']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Invitation to {self.email} for {self.family.name}"

    def is_expired(self):
        """Check if the invitation has expired."""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if the invitation is valid (pending and not expired)."""
        return self.status == 'pending' and not self.is_expired()

    def mark_accepted(self):
        """Mark the invitation as accepted."""
        self.status = 'accepted'
        self.save(update_fields=['status'])
        logger.info(
            "invitation_accepted",
            invitation_id=str(self.id),
            family_id=str(self.family.id),
            email=self.email
        )

    def mark_expired(self):
        """Mark the invitation as expired."""
        self.status = 'expired'
        self.save(update_fields=['status'])
        logger.info(
            "invitation_expired",
            invitation_id=str(self.id),
            family_id=str(self.family.id),
            email=self.email
        )

    def save(self, *args, **kwargs):
        """Override save to set expiration date if not set."""
        if not self.expires_at:
            # Default: 7 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
