"""
Tests for budget app.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .models import BudgetCategory, BudgetItem

User = get_user_model()


class BudgetCategoryModelTest(TestCase):
    """Tests for BudgetCategory model."""

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

        self.category = BudgetCategory.objects.create(
            trip=self.trip, name="Lodging", color_code="#2E86AB", order=1
        )

    def test_category_creation(self):
        """Test creating a budget category."""
        self.assertEqual(self.category.name, "Lodging")
        self.assertEqual(self.category.trip, self.trip)
        self.assertEqual(self.category.color_code, "#2E86AB")
        self.assertEqual(self.category.order, 1)

    def test_category_str(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), "Lodging (Hawaii 2025)")

    def test_get_total_estimated(self):
        """Test calculating total estimated amount."""
        BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Hotel",
            estimated_amount=Decimal("1000.00"),
            created_by=self.user,
        )
        BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Resort fee",
            estimated_amount=Decimal("200.00"),
            created_by=self.user,
        )

        self.assertEqual(self.category.get_total_estimated(), Decimal("1200.00"))

    def test_get_total_actual(self):
        """Test calculating total actual amount."""
        BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Hotel",
            estimated_amount=Decimal("1000.00"),
            actual_amount=Decimal("950.00"),
            created_by=self.user,
        )
        BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Resort fee",
            estimated_amount=Decimal("200.00"),
            actual_amount=Decimal("210.00"),
            created_by=self.user,
        )

        self.assertEqual(self.category.get_total_actual(), Decimal("1160.00"))


class BudgetItemModelTest(TestCase):
    """Tests for BudgetItem model."""

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

        self.category = BudgetCategory.objects.create(trip=self.trip, name="Lodging")

        self.budget_item = BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Hotel Accommodation",
            estimated_amount=Decimal("1000.00"),
            created_by=self.user,
        )

    def test_budget_item_creation(self):
        """Test creating a budget item."""
        self.assertEqual(self.budget_item.description, "Hotel Accommodation")
        self.assertEqual(self.budget_item.trip, self.trip)
        self.assertEqual(self.budget_item.category, self.category)
        self.assertEqual(self.budget_item.estimated_amount, Decimal("1000.00"))
        self.assertIsNone(self.budget_item.actual_amount)

    def test_budget_item_str(self):
        """Test budget item string representation."""
        self.assertEqual(str(self.budget_item), "Hotel Accommodation - Hawaii 2025")

    def test_is_paid(self):
        """Test is_paid property."""
        self.assertFalse(self.budget_item.is_paid)

        self.budget_item.actual_amount = Decimal("950.00")
        self.budget_item.save()
        self.assertTrue(self.budget_item.is_paid)

    def test_variance(self):
        """Test variance calculation."""
        self.assertIsNone(self.budget_item.variance)

        self.budget_item.actual_amount = Decimal("950.00")
        self.budget_item.save()
        self.assertEqual(self.budget_item.variance, Decimal("50.00"))  # Under budget

        self.budget_item.actual_amount = Decimal("1100.00")
        self.budget_item.save()
        self.assertEqual(self.budget_item.variance, Decimal("-100.00"))  # Over budget

    def test_variance_percentage(self):
        """Test variance percentage calculation."""
        self.assertIsNone(self.budget_item.variance_percentage)

        self.budget_item.actual_amount = Decimal("950.00")
        self.budget_item.save()
        self.assertEqual(self.budget_item.variance_percentage, Decimal("5.00"))  # 5% under

        self.budget_item.actual_amount = Decimal("1100.00")
        self.budget_item.save()
        self.assertEqual(self.budget_item.variance_percentage, Decimal("-10.00"))  # 10% over
