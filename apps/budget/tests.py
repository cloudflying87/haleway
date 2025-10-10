"""
Comprehensive tests for budget app.
Tests models, forms, views, AJAX endpoints, and CSV import functionality.
"""

import io
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.families.models import Family, FamilyMember
from apps.trips.models import Trip

from .forms import BudgetCategoryForm, BudgetCSVImportForm, BudgetItemForm
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

    def test_category_absolute_url(self):
        """Test get_absolute_url."""
        url = self.category.get_absolute_url()
        self.assertEqual(url, reverse("budget:category_update", kwargs={"pk": self.category.pk}))

    def test_category_unique_constraint(self):
        """Test unique constraint on trip + name."""
        with self.assertRaises(Exception):
            BudgetCategory.objects.create(trip=self.trip, name="Lodging")

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

    def test_get_total_with_no_items(self):
        """Test totals with no items."""
        self.assertEqual(self.category.get_total_estimated(), Decimal("0.00"))
        self.assertEqual(self.category.get_total_actual(), Decimal("0.00"))


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

    def test_budget_item_absolute_url(self):
        """Test get_absolute_url."""
        url = self.budget_item.get_absolute_url()
        self.assertEqual(url, reverse("budget:item_detail", kwargs={"pk": self.budget_item.pk}))

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

    def test_variance_percentage_with_zero_estimated(self):
        """Test variance percentage when estimated is zero."""
        item = BudgetItem.objects.create(
            trip=self.trip,
            description="Free item",
            estimated_amount=Decimal("0.00"),
            actual_amount=Decimal("0.00"),
            created_by=self.user,
        )
        self.assertIsNone(item.variance_percentage)

    def test_item_without_category(self):
        """Test creating item without category."""
        item = BudgetItem.objects.create(
            trip=self.trip,
            description="Uncategorized expense",
            estimated_amount=Decimal("50.00"),
            created_by=self.user,
        )
        self.assertIsNone(item.category)


class BudgetCategoryFormTest(TestCase):
    """Tests for BudgetCategoryForm."""

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

    def test_valid_form(self):
        """Test form with valid data."""
        form = BudgetCategoryForm(
            data={"name": "Food", "color_code": "#FF6B6B", "order": 2}, trip=self.trip
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_category_name(self):
        """Test validation for duplicate category name."""
        BudgetCategory.objects.create(trip=self.trip, name="Food")

        form = BudgetCategoryForm(data={"name": "Food", "color_code": "#FF6B6B"}, trip=self.trip)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_short_category_name(self):
        """Test validation for short category name."""
        form = BudgetCategoryForm(data={"name": "A", "color_code": "#FF6B6B"}, trip=self.trip)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed from name."""
        form = BudgetCategoryForm(
            data={"name": "  Food  ", "color_code": "#FF6B6B"}, trip=self.trip
        )
        self.assertTrue(form.is_valid())
        category = form.save()
        self.assertEqual(category.name, "Food")


class BudgetItemFormTest(TestCase):
    """Tests for BudgetItemForm."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        FamilyMember.objects.create(family=self.family, user=self.user, role="owner")
        FamilyMember.objects.create(family=self.family, user=self.other_user, role="member")

        self.trip = Trip.objects.create(
            family=self.family,
            name="Hawaii 2025",
            destination_name="Maui",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            created_by=self.user,
        )

        self.category = BudgetCategory.objects.create(trip=self.trip, name="Food")

    def test_valid_form_basic(self):
        """Test form with basic valid data."""
        form = BudgetItemForm(
            data={
                "category": self.category.pk,
                "description": "Dinner at restaurant",
                "estimated_amount": "120.00",
            },
            trip=self.trip,
            created_by=self.user,
            family_members=User.objects.filter(pk=self.user.pk),
        )
        self.assertTrue(form.is_valid())

    def test_valid_form_with_payment(self):
        """Test form with payment information."""
        form = BudgetItemForm(
            data={
                "category": self.category.pk,
                "description": "Dinner",
                "estimated_amount": "120.00",
                "actual_amount": "135.00",
                "paid_by": self.user.pk,
                "payment_date": date.today(),
            },
            trip=self.trip,
            created_by=self.user,
            family_members=User.objects.filter(pk__in=[self.user.pk, self.other_user.pk]),
        )
        self.assertTrue(form.is_valid())

    def test_negative_estimated_amount(self):
        """Test validation for negative estimated amount."""
        form = BudgetItemForm(
            data={"description": "Test", "estimated_amount": "-100.00"},
            trip=self.trip,
            created_by=self.user,
            family_members=User.objects.filter(pk=self.user.pk),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("estimated_amount", form.errors)

    def test_actual_without_paid_by(self):
        """Test that actual amount requires paid_by."""
        form = BudgetItemForm(
            data={
                "description": "Test",
                "estimated_amount": "100.00",
                "actual_amount": "110.00",
                # Missing paid_by and payment_date
            },
            trip=self.trip,
            created_by=self.user,
            family_members=User.objects.filter(pk=self.user.pk),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("paid_by", form.errors)
        self.assertIn("payment_date", form.errors)

    def test_short_description(self):
        """Test validation for short description."""
        form = BudgetItemForm(
            data={"description": "A", "estimated_amount": "100.00"},
            trip=self.trip,
            created_by=self.user,
            family_members=User.objects.filter(pk=self.user.pk),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)


class BudgetCSVImportFormTest(TestCase):
    """Tests for BudgetCSVImportForm."""

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

        self.category = BudgetCategory.objects.create(trip=self.trip, name="Food")

    def test_valid_csv(self):
        """Test parsing valid CSV file."""
        csv_content = """description,estimated_amount,category,actual_amount,paid_by,payment_date,notes
Hotel,1500.00,,,,,
Dinner,120.00,Food,135.00,testuser,2025-10-05,Great place"""

        csv_file = SimpleUploadedFile(
            "test.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        form = BudgetCSVImportForm(
            data={},
            files={"csv_file": csv_file},
            trip=self.trip,
            family_members=User.objects.filter(pk=self.user.pk),
        )

        self.assertTrue(form.is_valid())
        items_data = form.parse_csv()
        self.assertEqual(len(items_data), 2)
        self.assertEqual(items_data[0]["description"], "Hotel")
        self.assertEqual(items_data[0]["estimated_amount"], Decimal("1500.00"))
        self.assertEqual(items_data[1]["description"], "Dinner")
        self.assertEqual(items_data[1]["category"], self.category)

    def test_missing_required_columns(self):
        """Test CSV with missing required columns."""
        csv_content = """description
Hotel"""

        csv_file = SimpleUploadedFile(
            "test.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        form = BudgetCSVImportForm(
            data={}, files={"csv_file": csv_file}, trip=self.trip, family_members=None
        )

        self.assertFalse(form.is_valid())

    def test_invalid_amount(self):
        """Test CSV with invalid amount."""
        csv_content = """description,estimated_amount
Hotel,not_a_number"""

        csv_file = SimpleUploadedFile(
            "test.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        form = BudgetCSVImportForm(
            data={}, files={"csv_file": csv_file}, trip=self.trip, family_members=None
        )

        self.assertFalse(form.is_valid())

    def test_file_size_limit(self):
        """Test CSV file size validation."""
        # Create a file larger than 5MB
        large_content = "description,estimated_amount\n" + ("test,100.00\n" * 100000)
        csv_file = SimpleUploadedFile(
            "large.csv", large_content.encode("utf-8"), content_type="text/csv"
        )

        form = BudgetCSVImportForm(
            data={}, files={"csv_file": csv_file}, trip=self.trip, family_members=None
        )

        self.assertFalse(form.is_valid())


class BudgetViewsTest(TestCase):
    """Tests for budget views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="testpass123"
        )
        self.family = Family.objects.create(name="Test Family")
        FamilyMember.objects.create(family=self.family, user=self.user, role="member")
        FamilyMember.objects.create(family=self.family, user=self.admin, role="admin")

        self.trip = Trip.objects.create(
            family=self.family,
            name="Hawaii 2025",
            destination_name="Maui",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=37),
            created_by=self.user,
        )

        self.category = BudgetCategory.objects.create(trip=self.trip, name="Food")

        self.budget_item = BudgetItem.objects.create(
            trip=self.trip,
            category=self.category,
            description="Dinner",
            estimated_amount=Decimal("120.00"),
            created_by=self.user,
        )

    def test_budget_overview_view(self):
        """Test budget overview page."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:budget_overview", kwargs={"trip_pk": self.trip.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Budget Tracker")
        self.assertContains(response, "Dinner")
        self.assertContains(response, "$120.00")

    def test_budget_overview_requires_login(self):
        """Test that budget overview requires login."""
        url = reverse("budget:budget_overview", kwargs={"trip_pk": self.trip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_item_ajax(self):
        """Test AJAX add item endpoint."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:add_item_ajax", kwargs={"trip_pk": self.trip.pk})

        data = {
            "description": "Lunch",
            "estimated_amount": "50.00",
            "category": self.category.pk,
        }

        response = self.client.post(url, data, content_type="application/x-www-form-urlencoded")

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertIn("Lunch", json_data["message"])

        # Verify item was created
        self.assertTrue(BudgetItem.objects.filter(description="Lunch").exists())

    def test_add_item_ajax_validation(self):
        """Test AJAX add item with invalid data."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:add_item_ajax", kwargs={"trip_pk": self.trip.pk})

        data = {
            "description": "",  # Invalid - empty
            "estimated_amount": "-50.00",  # Invalid - negative
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertIn("errors", json_data)

    def test_csv_import_view_get(self):
        """Test CSV import page GET request."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:import_csv", kwargs={"trip_pk": self.trip.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import Budget Items from CSV")
        self.assertContains(response, "CSV Format Guide")

    def test_csv_import_post(self):
        """Test CSV import with valid file."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:import_csv", kwargs={"trip_pk": self.trip.pk})

        csv_content = """description,estimated_amount,category,actual_amount,paid_by,payment_date,notes
Hotel,1500.00,,,,,
Snacks,50.00,Food,,,,"Trail mix and granola bars"""

        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "test.csv"

        response = self.client.post(url, {"csv_file": csv_file}, follow=True)

        self.assertEqual(response.status_code, 200)
        # Should redirect to budget overview
        self.assertContains(response, "Successfully imported 2 budget items")

        # Verify items were created
        self.assertTrue(BudgetItem.objects.filter(description="Hotel").exists())
        self.assertTrue(BudgetItem.objects.filter(description="Snacks").exists())

    def test_member_cannot_delete(self):
        """Test that regular members cannot delete items."""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("budget:item_delete", kwargs={"pk": self.budget_item.pk})
        response = self.client.get(url)

        # Should not have access
        self.assertEqual(response.status_code, 404)

    def test_admin_can_delete(self):
        """Test that admins can delete items."""
        self.client.login(username="admin", password="testpass123")
        url = reverse("budget:item_delete", kwargs={"pk": self.budget_item.pk})
        response = self.client.get(url)

        # Should have access to delete confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure")


class BudgetIntegrationTest(TestCase):
    """Integration tests for budget functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
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

    def test_full_budget_workflow(self):
        """Test complete budget workflow: create category, add items, view totals."""
        self.client.login(username="testuser", password="testpass123")

        # Create category
        category_url = reverse("budget:category_create", kwargs={"trip_pk": self.trip.pk})
        response = self.client.post(
            category_url,
            {"name": "Transportation", "color_code": "#2E86AB", "order": 1},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        category = BudgetCategory.objects.get(trip=self.trip, name="Transportation")

        # Add first item via AJAX
        ajax_url = reverse("budget:add_item_ajax", kwargs={"trip_pk": self.trip.pk})
        response = self.client.post(
            ajax_url,
            {
                "description": "Flight tickets",
                "estimated_amount": "800.00",
                "category": category.pk,
            },
        )
        json_data = response.json()
        self.assertTrue(json_data["success"])

        # Add second item
        response = self.client.post(
            ajax_url,
            {
                "description": "Rental car",
                "estimated_amount": "350.00",
                "category": category.pk,
                "actual_amount": "375.00",
                "paid_by": self.user.pk,
                "payment_date": date.today().isoformat(),
            },
        )
        json_data = response.json()
        self.assertTrue(json_data["success"])

        # View budget overview
        overview_url = reverse("budget:budget_overview", kwargs={"trip_pk": self.trip.pk})
        response = self.client.get(overview_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flight tickets")
        self.assertContains(response, "Rental car")
        self.assertContains(response, "$1,150.00")  # Total estimated
        self.assertContains(response, "$375.00")  # Total actual
