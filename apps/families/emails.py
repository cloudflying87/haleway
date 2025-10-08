"""
Email utilities for family invitations.
"""

import structlog
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

logger = structlog.get_logger(__name__)


def send_family_invitation_email(invitation, request=None):
    """
    Send an invitation email to join a family.

    Args:
        invitation: FamilyInvitation instance
        request: HttpRequest object (optional, used to build absolute URLs)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Build the acceptance URL
        accept_path = reverse("families:accept_invitation", kwargs={"token": invitation.token})

        if request:
            accept_url = request.build_absolute_uri(accept_path)
        else:
            # Fallback: use DOMAIN_NAME from settings or localhost
            domain = getattr(settings, "DOMAIN_NAME", "localhost:8000")
            protocol = "https" if not settings.DEBUG else "http"
            accept_url = f"{protocol}://{domain}{accept_path}"

        # Render email content
        context = {
            "invitation": invitation,
            "family_name": invitation.family.name,
            "invited_by": invitation.invited_by.get_full_name() or invitation.invited_by.email,
            "accept_url": accept_url,
            "expires_at": invitation.expires_at,
        }

        # Render HTML email
        html_message = render_to_string("families/emails/invitation_email.html", context)

        # Create plain text version
        plain_message = strip_tags(html_message)

        # Send email
        subject = f"You've been invited to join {invitation.family.name} on HaleWay"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [invitation.email]

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            "invitation_email_sent",
            invitation_id=str(invitation.id),
            family_id=str(invitation.family.id),
            email=invitation.email,
            accept_url=accept_url,
        )

        return True

    except Exception as e:
        logger.error(
            "invitation_email_failed",
            invitation_id=str(invitation.id),
            family_id=str(invitation.family.id),
            email=invitation.email,
            error=str(e),
            exc_info=True,
        )
        return False
