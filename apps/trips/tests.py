"""
Tests for trips app.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.families.models import Family, FamilyMember

from .models import Resort, Trip

User = get_user_model()


class TripModelTest(TestCase):
    """Tests for Trip model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        FamilyMember.objects.create(family=self.family, user=self.user, role="owner")

        self.trip = Trip.objects.create(
            family=self.family,
            name="Hawaii 2025",
            destination_name="Maui",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            created_by=self.user,
        )

    def test_trip_creation(self):
        """Test creating a trip."""
        self.assertEqual(self.trip.name, "Hawaii 2025")
        self.assertEqual(self.trip.destination_name, "Maui")
        self.assertEqual(self.trip.family, self.family)
        self.assertEqual(self.trip.status, "planning")
        self.assertIsNotNone(self.trip.id)

    def test_trip_str(self):
        """Test trip string representation."""
        self.assertEqual(str(self.trip), "Hawaii 2025 - Maui")

    def test_duration_days(self):
        """Test trip duration calculation."""
        self.assertEqual(self.trip.duration_days(), 8)  # 7 nights, 8 days

    def test_is_upcoming(self):
        """Test is_upcoming method."""
        self.assertTrue(self.trip.is_upcoming())

        # Create past trip
        past_trip = Trip.objects.create(
            family=self.family,
            name="Past Trip",
            destination_name="Past",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=23),
            created_by=self.user,
        )
        self.assertFalse(past_trip.is_upcoming())

    def test_is_active(self):
        """Test is_active method."""
        self.assertFalse(self.trip.is_active())

        # Create active trip
        active_trip = Trip.objects.create(
            family=self.family,
            name="Active Trip",
            destination_name="Active",
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=5),
            created_by=self.user,
        )
        self.assertTrue(active_trip.is_active())

    def test_is_past(self):
        """Test is_past method."""
        self.assertFalse(self.trip.is_past())

        # Create past trip
        past_trip = Trip.objects.create(
            family=self.family,
            name="Past Trip",
            destination_name="Past",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=23),
            created_by=self.user,
        )
        self.assertTrue(past_trip.is_past())


class ResortModelTest(TestCase):
    """Tests for Resort model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        FamilyMember.objects.create(family=self.family, user=self.user, role="owner")

        self.trip = Trip.objects.create(
            family=self.family,
            name="Hawaii 2025",
            destination_name="Maui",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            created_by=self.user,
        )

        self.resort = Resort.objects.create(
            trip=self.trip,
            name="Grand Wailea Resort",
            website_url="https://grandwailea.com",
            address_line1="3850 Wailea Alanui Dr",
            city="Wailea",
            state="HI",
            zip_code="96753",
            country="US",
            latitude=20.6845,
            longitude=-156.4455,
        )

    def test_resort_creation(self):
        """Test creating a resort."""
        self.assertEqual(self.resort.name, "Grand Wailea Resort")
        self.assertEqual(self.resort.trip, self.trip)
        self.assertEqual(self.resort.city, "Wailea")
        self.assertEqual(self.resort.state, "HI")

    def test_resort_str(self):
        """Test resort string representation."""
        self.assertIn("Grand Wailea Resort", str(self.resort))

    def test_get_full_address(self):
        """Test get_full_address method."""
        full_address = self.resort.get_full_address()
        self.assertIn("3850 Wailea Alanui Dr", full_address)
        self.assertIn("Wailea", full_address)
        self.assertIn("HI", full_address)

    def test_has_coordinates(self):
        """Test checking for coordinates."""
        self.assertIsNotNone(self.resort.latitude)
        self.assertIsNotNone(self.resort.longitude)

        resort_no_coords = Resort.objects.create(
            trip=Trip.objects.create(
                family=self.family,
                name="Test Trip 2",
                destination_name="Test",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                created_by=self.user,
            ),
            name="Resort No Coords",
            city="City",
            state="ST",
        )
        self.assertIsNone(resort_no_coords.latitude)
        self.assertIsNone(resort_no_coords.longitude)

    def test_one_resort_per_trip(self):
        """Test that a trip can only have one resort."""
        with self.assertRaises(Exception):
            Resort.objects.create(trip=self.trip, name="Another Resort", city="City", state="ST")
