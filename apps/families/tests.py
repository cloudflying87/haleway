"""
Tests for families app.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Family, FamilyInvitation, FamilyMember

User = get_user_model()


class FamilyModelTest(TestCase):
    """Tests for Family model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        self.membership = FamilyMember.objects.create(
            family=self.family, user=self.user, role="owner"
        )

    def test_family_creation(self):
        """Test creating a family."""
        self.assertEqual(self.family.name, "Test Family")
        self.assertIsNotNone(self.family.id)
        self.assertIsInstance(self.family.created_at, type(timezone.now()))

    def test_family_str(self):
        """Test family string representation."""
        self.assertEqual(str(self.family), "Test Family")

    def test_get_owner(self):
        """Test getting family owner."""
        owner = self.family.get_owner()
        self.assertEqual(owner, self.user)

    def test_get_admins(self):
        """Test getting family admins."""
        admin_user = User.objects.create_user(
            username="admin", email="admin@example.com", password="testpass123"
        )
        FamilyMember.objects.create(family=self.family, user=admin_user, role="admin")

        admins = self.family.get_admins()
        self.assertEqual(admins.count(), 2)  # Owner + Admin

    def test_get_all_members(self):
        """Test getting all family members."""
        member_user = User.objects.create_user(
            username="member", email="member@example.com", password="testpass123"
        )
        FamilyMember.objects.create(family=self.family, user=member_user, role="member")

        members = self.family.get_all_members()
        self.assertEqual(members.count(), 2)

    def test_member_count(self):
        """Test member count method."""
        self.assertEqual(self.family.member_count(), 1)

        User.objects.create_user(
            username="member2", email="member2@example.com", password="testpass123"
        )
        # Count should still be 1 until added to family


class FamilyMemberModelTest(TestCase):
    """Tests for FamilyMember model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        self.membership = FamilyMember.objects.create(
            family=self.family, user=self.user, role="owner"
        )

    def test_family_member_creation(self):
        """Test creating a family member."""
        self.assertEqual(self.membership.family, self.family)
        self.assertEqual(self.membership.user, self.user)
        self.assertEqual(self.membership.role, "owner")

    def test_is_owner(self):
        """Test is_owner method."""
        self.assertTrue(self.membership.is_owner())

        member = FamilyMember.objects.create(
            family=self.family,
            user=User.objects.create_user(
                username="member", email="member@example.com", password="testpass123"
            ),
            role="member",
        )
        self.assertFalse(member.is_owner())

    def test_is_admin(self):
        """Test is_admin method."""
        self.assertTrue(self.membership.is_admin())  # Owner is admin

        admin = FamilyMember.objects.create(
            family=self.family,
            user=User.objects.create_user(
                username="admin", email="admin@example.com", password="testpass123"
            ),
            role="admin",
        )
        self.assertTrue(admin.is_admin())

        member = FamilyMember.objects.create(
            family=self.family,
            user=User.objects.create_user(
                username="member", email="member@example.com", password="testpass123"
            ),
            role="member",
        )
        self.assertFalse(member.is_admin())

    def test_unique_user_per_family(self):
        """Test that a user can't be in the same family twice."""
        with self.assertRaises(Exception):
            FamilyMember.objects.create(family=self.family, user=self.user, role="member")


class FamilyInvitationModelTest(TestCase):
    """Tests for FamilyInvitation model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        FamilyMember.objects.create(family=self.family, user=self.user, role="owner")

    def test_invitation_creation(self):
        """Test creating an invitation."""
        invitation = FamilyInvitation.objects.create(
            family=self.family, email="invite@example.com", invited_by=self.user
        )

        self.assertEqual(invitation.family, self.family)
        self.assertEqual(invitation.email, "invite@example.com")
        self.assertEqual(invitation.invited_by, self.user)
        self.assertEqual(invitation.status, "pending")
        self.assertIsNotNone(invitation.token)
        self.assertIsNotNone(invitation.expires_at)

    def test_invitation_expiration(self):
        """Test invitation expiration."""
        invitation = FamilyInvitation.objects.create(
            family=self.family,
            email="invite@example.com",
            invited_by=self.user,
            expires_at=timezone.now() - timezone.timedelta(days=1),  # Already expired
        )

        self.assertFalse(invitation.is_valid())

    def test_invitation_valid(self):
        """Test valid invitation."""
        invitation = FamilyInvitation.objects.create(
            family=self.family, email="invite@example.com", invited_by=self.user
        )

        self.assertTrue(invitation.is_valid())

    def test_mark_accepted(self):
        """Test marking invitation as accepted."""
        invitation = FamilyInvitation.objects.create(
            family=self.family, email="invite@example.com", invited_by=self.user
        )

        invitation.mark_accepted()
        self.assertEqual(invitation.status, "accepted")

    def test_mark_expired(self):
        """Test marking invitation as expired."""
        invitation = FamilyInvitation.objects.create(
            family=self.family, email="invite@example.com", invited_by=self.user
        )

        invitation.mark_expired()
        self.assertEqual(invitation.status, "expired")
