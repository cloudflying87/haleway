"""
Tests for activities app.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .models import Activity

User = get_user_model()


class ActivityModelTest(TestCase):
    """Tests for Activity model."""

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

        self.activity = Activity.objects.create(
            trip=self.trip,
            name="Snorkeling at Molokini Crater",
            description="Half-day snorkeling tour",
            address_line1="Maalaea Harbor",
            city="Wailuku",
            state="HI",
            zip_code="96793",
            estimated_cost=Decimal("129.99"),
            estimated_duration=240,  # 4 hours
            distance_from_resort=Decimal("12.50"),
            travel_time_from_resort=25,
            pre_trip_priority=1,
            created_by=self.user,
        )

    def test_activity_creation(self):
        """Test creating an activity."""
        self.assertEqual(self.activity.name, "Snorkeling at Molokini Crater")
        self.assertEqual(self.activity.trip, self.trip)
        self.assertEqual(self.activity.estimated_cost, Decimal("129.99"))
        self.assertEqual(self.activity.pre_trip_priority, 1)
        self.assertFalse(self.activity.is_favorite)

    def test_activity_str(self):
        """Test activity string representation."""
        self.assertEqual(str(self.activity), "Snorkeling at Molokini Crater - Hawaii 2025")

    def test_get_full_address(self):
        """Test get_full_address method."""
        full_address = self.activity.get_full_address()
        self.assertIn("Maalaea Harbor", full_address)
        self.assertIn("Wailuku", full_address)
        self.assertIn("HI", full_address)

    def test_has_rating(self):
        """Test has_rating method."""
        self.assertFalse(self.activity.has_rating())

        self.activity.post_trip_rating = 5
        self.activity.save()
        self.assertTrue(self.activity.has_rating())

    def test_get_duration_display(self):
        """Test get_duration_display method."""
        self.assertEqual(self.activity.get_duration_display(), "4h")

        self.activity.estimated_duration = 90  # 1.5 hours
        self.assertEqual(self.activity.get_duration_display(), "1h 30m")

        self.activity.estimated_duration = 45  # 45 minutes
        self.assertEqual(self.activity.get_duration_display(), "45m")

        self.activity.estimated_duration = None
        self.assertEqual(self.activity.get_duration_display(), "Unknown")

    def test_get_travel_time_display(self):
        """Test get_travel_time_display method."""
        self.assertEqual(self.activity.get_travel_time_display(), "25m")

        self.activity.travel_time_from_resort = 90  # 1.5 hours
        self.assertEqual(self.activity.get_travel_time_display(), "1h 30m")

        self.activity.travel_time_from_resort = 120  # 2 hours
        self.assertEqual(self.activity.get_travel_time_display(), "2h")

        self.activity.travel_time_from_resort = None
        self.assertEqual(self.activity.get_travel_time_display(), "Unknown")

    def test_post_trip_rating(self):
        """Test post-trip rating functionality."""
        # Initially no rating
        self.assertIsNone(self.activity.post_trip_rating)
        self.assertFalse(self.activity.has_rating())

        # Add rating
        self.activity.post_trip_rating = 4
        self.activity.post_trip_notes = "Great experience! Would recommend."
        self.activity.is_favorite = True
        self.activity.save()

        self.assertEqual(self.activity.post_trip_rating, 4)
        self.assertTrue(self.activity.has_rating())
        self.assertTrue(self.activity.is_favorite)
        self.assertEqual(self.activity.post_trip_notes, "Great experience! Would recommend.")

    def test_priority_ordering(self):
        """Test that activities are ordered by priority."""
        activity1 = Activity.objects.create(
            trip=self.trip,
            name="Activity 1",
            pre_trip_priority=3,
            created_by=self.user,
        )
        activity2 = Activity.objects.create(
            trip=self.trip,
            name="Activity 2",
            pre_trip_priority=1,
            created_by=self.user,
        )
        activity3 = Activity.objects.create(
            trip=self.trip,
            name="Activity 3",
            pre_trip_priority=2,
            created_by=self.user,
        )

        # Get all activities ordered
        activities = list(Activity.objects.filter(trip=self.trip))

        # Should be ordered by pre_trip_priority (ascending)
        # Note: self.activity has priority 1, so it should be first
        self.assertEqual(activities[0].pre_trip_priority, 1)
        self.assertEqual(activities[1].pre_trip_priority, 1)
        self.assertEqual(activities[2].pre_trip_priority, 2)
        self.assertEqual(activities[3].pre_trip_priority, 3)

    def test_favorite_flag(self):
        """Test favorite flag functionality."""
        self.assertFalse(self.activity.is_favorite)

        # Mark as favorite
        self.activity.is_favorite = True
        self.activity.save()

        self.assertTrue(self.activity.is_favorite)

        # Unmark as favorite
        self.activity.is_favorite = False
        self.activity.save()

        self.assertFalse(self.activity.is_favorite)
