"""
Tests for notes app.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .models import Note, NoteCategory

User = get_user_model()


class NoteCategoryModelTest(TestCase):
    """Tests for NoteCategory model."""

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

        self.category = NoteCategory.objects.create(
            trip=self.trip, name="Transportation", color_code="#2E86AB", order=1
        )

    def test_category_creation(self):
        """Test creating a note category."""
        self.assertEqual(self.category.name, "Transportation")
        self.assertEqual(self.category.trip, self.trip)
        self.assertEqual(self.category.color_code, "#2E86AB")
        self.assertEqual(self.category.order, 1)

    def test_category_str(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), "Transportation (Hawaii 2025)")

    def test_category_ordering(self):
        """Test that categories are ordered correctly."""
        cat1 = NoteCategory.objects.create(trip=self.trip, name="Food", order=3)
        cat2 = NoteCategory.objects.create(trip=self.trip, name="Emergency", order=1)
        cat3 = NoteCategory.objects.create(trip=self.trip, name="Activities", order=2)

        categories = list(NoteCategory.objects.filter(trip=self.trip))

        # Should be ordered by order field, then name
        # self.category has order=1, cat2 has order=1, cat3 has order=2, cat1 has order=3
        # So: Emergency (order 1), Transportation (order 1), Activities (order 2), Food (order 3)
        # When order is same, sorts by name alphabetically
        self.assertEqual(categories[0].name, "Emergency")
        self.assertEqual(categories[1].name, "Transportation")
        self.assertEqual(categories[2].name, "Activities")
        self.assertEqual(categories[3].name, "Food")

    def test_unique_category_per_trip(self):
        """Test that category names must be unique per trip."""
        with self.assertRaises(Exception):
            NoteCategory.objects.create(trip=self.trip, name="Transportation", color_code="#FF6B6B")


class NoteModelTest(TestCase):
    """Tests for Note model."""

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

        self.category = NoteCategory.objects.create(
            trip=self.trip, name="Transportation", color_code="#2E86AB"
        )

        self.note = Note.objects.create(
            trip=self.trip,
            category=self.category,
            title="Airport Transfer",
            content="Book shuttle from airport to hotel. Confirmation #12345",
            created_by=self.user,
        )

    def test_note_creation(self):
        """Test creating a note."""
        self.assertEqual(self.note.title, "Airport Transfer")
        self.assertEqual(self.note.trip, self.trip)
        self.assertEqual(self.note.category, self.category)
        self.assertFalse(self.note.is_pinned)

    def test_note_str(self):
        """Test note string representation."""
        self.assertEqual(str(self.note), "Airport Transfer - Hawaii 2025")

    def test_note_without_category(self):
        """Test creating a note without a category."""
        uncategorized_note = Note.objects.create(
            trip=self.trip,
            title="Random Thought",
            content="Don't forget sunscreen!",
            created_by=self.user,
        )

        self.assertIsNone(uncategorized_note.category)
        self.assertEqual(uncategorized_note.trip, self.trip)

    def test_pinned_notes(self):
        """Test pinning and unpinning notes."""
        self.assertFalse(self.note.is_pinned)

        # Pin the note
        self.note.is_pinned = True
        self.note.save()

        self.assertTrue(self.note.is_pinned)

        # Unpin the note
        self.note.is_pinned = False
        self.note.save()

        self.assertFalse(self.note.is_pinned)

    def test_note_ordering(self):
        """Test that notes are ordered with pinned notes first."""
        note1 = Note.objects.create(
            trip=self.trip,
            title="Regular Note 1",
            content="Content 1",
            is_pinned=False,
            created_by=self.user,
        )
        note2 = Note.objects.create(
            trip=self.trip,
            title="Pinned Note",
            content="Important!",
            is_pinned=True,
            created_by=self.user,
        )
        note3 = Note.objects.create(
            trip=self.trip,
            title="Regular Note 2",
            content="Content 2",
            is_pinned=False,
            created_by=self.user,
        )

        # Get all notes ordered
        notes = list(Note.objects.filter(trip=self.trip))

        # First note should be pinned
        self.assertTrue(notes[0].is_pinned)
        self.assertEqual(notes[0].title, "Pinned Note")

        # Other notes should be unpinned
        self.assertFalse(notes[1].is_pinned)
        self.assertFalse(notes[2].is_pinned)
        self.assertFalse(notes[3].is_pinned)

    def test_category_deletion_sets_null(self):
        """Test that deleting a category sets note category to null."""
        self.assertEqual(self.note.category, self.category)

        # Delete the category
        self.category.delete()

        # Refresh note from database
        self.note.refresh_from_db()

        # Category should be null
        self.assertIsNone(self.note.category)
