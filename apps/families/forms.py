"""
Forms for family management.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Family, FamilyInvitation


class FamilyForm(forms.ModelForm):
    """Form for creating and editing families."""

    class Meta:
        model = Family
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., The Smith Family',
                'required': True
            })
        }
        labels = {
            'name': _('Family Name')
        }
        help_texts = {
            'name': _('Choose a name that all family members will recognize.')
        }

    def clean_name(self):
        """Validate family name."""
        name = self.cleaned_data.get('name')
        if not name or len(name.strip()) < 2:
            raise ValidationError(_('Family name must be at least 2 characters long.'))
        return name.strip()


class FamilyInvitationForm(forms.ModelForm):
    """Form for inviting family members."""

    class Meta:
        model = FamilyInvitation
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'family.member@example.com',
                'required': True
            })
        }
        labels = {
            'email': _('Email Address')
        }
        help_texts = {
            'email': _('We will send an invitation link to this email address.')
        }

    def __init__(self, *args, family=None, invited_by=None, **kwargs):
        """Initialize form with family and inviter."""
        super().__init__(*args, **kwargs)
        self.family = family
        self.invited_by = invited_by

    def clean_email(self):
        """Validate that email is not already a member or invited."""
        email = self.cleaned_data.get('email')

        if not self.family:
            raise ValidationError(_('Invalid family.'))

        # Check if user is already a family member
        from apps.accounts.models import User
        try:
            user = User.objects.get(email=email)
            if self.family.members.filter(user=user).exists():
                raise ValidationError(_('This email is already a member of your family.'))
        except User.DoesNotExist:
            pass

        # Check if there's already a pending invitation
        pending_invitation = FamilyInvitation.objects.filter(
            family=self.family,
            email=email,
            status='pending'
        ).first()

        if pending_invitation and pending_invitation.is_valid():
            raise ValidationError(_('An invitation has already been sent to this email.'))

        return email

    def save(self, commit=True):
        """Save the invitation with family and inviter."""
        invitation = super().save(commit=False)
        invitation.family = self.family
        invitation.invited_by = self.invited_by
        if commit:
            invitation.save()
        return invitation
