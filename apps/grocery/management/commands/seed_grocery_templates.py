import structlog
from django.core.management.base import BaseCommand

from apps.grocery.models import GroceryListTemplate, GroceryListTemplateItem

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Seed system grocery list templates"

    def handle(self, *_args, **_options):
        self.stdout.write("Seeding system grocery templates...")

        # Beach Trip Template
        beach_template, created = GroceryListTemplate.objects.get_or_create(
            name="Beach Trip Groceries",
            is_system_template=True,
            defaults={
                "description": "Grocery essentials for a relaxing beach vacation",
                "family": None,
                "created_by": None,
            },
        )

        if created:
            beach_items = [
                # Beverages
                ("Beverages", "Bottled Water", "2 cases"),
                ("Beverages", "Sports Drinks", "12 pack"),
                ("Beverages", "Juice Boxes", "1 box"),
                ("Beverages", "Coffee", "1 bag"),
                ("Beverages", "Iced Tea Mix", "1 container"),
                # Breakfast
                ("Breakfast", "Cereal", "2 boxes"),
                ("Breakfast", "Milk", "1 gallon"),
                ("Breakfast", "Yogurt", "6 pack"),
                ("Breakfast", "Fresh Fruit", ""),
                ("Breakfast", "Bagels", "1 bag"),
                ("Breakfast", "Cream Cheese", "1 tub"),
                # Snacks
                ("Snacks", "Chips", "3 bags"),
                ("Snacks", "Pretzels", "1 bag"),
                ("Snacks", "Granola Bars", "1 box"),
                ("Snacks", "Trail Mix", "2 bags"),
                ("Snacks", "Cookies", "1 pack"),
                ("Snacks", "Fresh Vegetables", ""),
                ("Snacks", "Hummus", "1 container"),
                # Lunch/Dinner
                ("Lunch/Dinner", "Sandwich Bread", "2 loaves"),
                ("Lunch/Dinner", "Deli Meat", "1 lb"),
                ("Lunch/Dinner", "Cheese Slices", "1 pack"),
                ("Lunch/Dinner", "Condiments", ""),
                ("Lunch/Dinner", "Hot Dogs", "1 pack"),
                ("Lunch/Dinner", "Hamburger Buns", "1 bag"),
                ("Lunch/Dinner", "Ground Beef", "2 lbs"),
                ("Lunch/Dinner", "Pasta", "2 boxes"),
                ("Lunch/Dinner", "Pasta Sauce", "2 jars"),
                # Household
                ("Household", "Paper Towels", "1 pack"),
                ("Household", "Napkins", "1 pack"),
                ("Household", "Trash Bags", "1 box"),
                ("Household", "Dish Soap", "1 bottle"),
                ("Household", "Sunscreen", "2 bottles"),
                ("Household", "Aloe Vera", "1 bottle"),
            ]

            for category, item_name, quantity in beach_items:
                GroceryListTemplateItem.objects.create(
                    template=beach_template,
                    category=category,
                    item_name=item_name,
                    quantity=quantity,
                )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created Beach Trip template with {len(beach_items)} items")
            )

        # Road Trip Template
        road_template, created = GroceryListTemplate.objects.get_or_create(
            name="Road Trip Groceries",
            is_system_template=True,
            defaults={
                "description": "Grab-and-go snacks and meals for road trips",
                "family": None,
                "created_by": None,
            },
        )

        if created:
            road_items = [
                # Beverages
                ("Beverages", "Bottled Water", "2 cases"),
                ("Beverages", "Sports Drinks", "12 pack"),
                ("Beverages", "Energy Drinks", "6 pack"),
                ("Beverages", "Juice Boxes", "1 box"),
                ("Beverages", "Coffee Pods", "1 box"),
                # Snacks
                ("Snacks", "Chips", "4 bags"),
                ("Snacks", "Crackers", "2 boxes"),
                ("Snacks", "Beef Jerky", "3 packs"),
                ("Snacks", "Protein Bars", "1 box"),
                ("Snacks", "Granola Bars", "1 box"),
                ("Snacks", "Mixed Nuts", "2 cans"),
                ("Snacks", "Candy", ""),
                ("Snacks", "Gum", "2 packs"),
                ("Snacks", "Fruit Pouches", "1 box"),
                # Quick Meals
                ("Quick Meals", "Pre-made Sandwiches", "6 pack"),
                ("Quick Meals", "String Cheese", "1 pack"),
                ("Quick Meals", "Crackers & Cheese", "6 pack"),
                ("Quick Meals", "Instant Oatmeal", "1 box"),
                ("Quick Meals", "Protein Shakes", "6 pack"),
                ("Quick Meals", "Apples", "1 bag"),
                ("Quick Meals", "Bananas", "1 bunch"),
                # Household
                ("Household", "Paper Towels", "1 pack"),
                ("Household", "Wet Wipes", "1 container"),
                ("Household", "Hand Sanitizer", "2 bottles"),
                ("Household", "Napkins", "1 pack"),
                ("Household", "Plastic Utensils", "1 pack"),
                ("Household", "Trash Bags", "1 box"),
            ]

            for category, item_name, quantity in road_items:
                GroceryListTemplateItem.objects.create(
                    template=road_template,
                    category=category,
                    item_name=item_name,
                    quantity=quantity,
                )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created Road Trip template with {len(road_items)} items")
            )

        # Camping Template
        camping_template, created = GroceryListTemplate.objects.get_or_create(
            name="Camping Groceries",
            is_system_template=True,
            defaults={
                "description": "Camping-friendly food and supplies",
                "family": None,
                "created_by": None,
            },
        )

        if created:
            camping_items = [
                # Beverages
                ("Beverages", "Bottled Water", "3 cases"),
                ("Beverages", "Hot Chocolate Mix", "1 box"),
                ("Beverages", "Coffee", "1 bag"),
                ("Beverages", "Sports Drinks", "12 pack"),
                # Breakfast
                ("Breakfast", "Pancake Mix", "1 box"),
                ("Breakfast", "Syrup", "1 bottle"),
                ("Breakfast", "Eggs", "2 dozen"),
                ("Breakfast", "Bacon", "2 packs"),
                ("Breakfast", "Instant Oatmeal", "1 box"),
                ("Breakfast", "Cereal Bars", "1 box"),
                # Snacks
                ("Snacks", "Trail Mix", "3 bags"),
                ("Snacks", "Granola Bars", "2 boxes"),
                ("Snacks", "Chips", "3 bags"),
                ("Snacks", "Marshmallows", "2 bags"),
                ("Snacks", "Graham Crackers", "2 boxes"),
                ("Snacks", "Chocolate Bars", "1 box"),
                ("Snacks", "Beef Jerky", "3 packs"),
                # Meals
                ("Meals", "Hot Dogs", "2 packs"),
                ("Meals", "Hamburger Buns", "2 bags"),
                ("Meals", "Ground Beef", "3 lbs"),
                ("Meals", "Canned Beans", "4 cans"),
                ("Meals", "Canned Chili", "2 cans"),
                ("Meals", "Pasta", "2 boxes"),
                ("Meals", "Canned Pasta Sauce", "2 jars"),
                ("Meals", "Aluminum Foil Meals", "6 pack"),
                # Produce
                ("Produce", "Potatoes", "5 lbs"),
                ("Produce", "Onions", "1 bag"),
                ("Produce", "Corn on Cob", "6 ears"),
                ("Produce", "Apples", "1 bag"),
                # Household
                ("Household", "Paper Towels", "2 packs"),
                ("Household", "Trash Bags", "1 box"),
                ("Household", "Aluminum Foil", "1 roll"),
                ("Household", "Plastic Wrap", "1 roll"),
                ("Household", "Ziplock Bags", "1 box"),
                ("Household", "Matches/Lighter", "2 boxes"),
                ("Household", "Bug Spray", "2 bottles"),
            ]

            for category, item_name, quantity in camping_items:
                GroceryListTemplateItem.objects.create(
                    template=camping_template,
                    category=category,
                    item_name=item_name,
                    quantity=quantity,
                )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created Camping template with {len(camping_items)} items")
            )

        # International Travel Template
        international_template, created = GroceryListTemplate.objects.get_or_create(
            name="International Travel Groceries",
            is_system_template=True,
            defaults={
                "description": "Travel-friendly snacks and essentials for international trips",
                "family": None,
                "created_by": None,
            },
        )

        if created:
            international_items = [
                # Snacks (for the flight/hotel room)
                ("Snacks", "Protein Bars", "1 box"),
                ("Snacks", "Granola Bars", "1 box"),
                ("Snacks", "Trail Mix", "2 bags"),
                ("Snacks", "Crackers", "2 boxes"),
                ("Snacks", "Gum", "2 packs"),
                ("Snacks", "Candy", ""),
                # Beverages (for after security/hotel)
                ("Beverages", "Electrolyte Packets", "1 box"),
                ("Beverages", "Tea Bags", "1 box"),
                ("Beverages", "Coffee Packets", "1 box"),
                ("Beverages", "Bottled Water", "1 case"),
                # Hotel Room Essentials
                ("Hotel Essentials", "Instant Oatmeal", "1 box"),
                ("Hotel Essentials", "Instant Noodles", "6 cups"),
                ("Hotel Essentials", "Peanut Butter", "1 jar"),
                ("Hotel Essentials", "Bread", "1 loaf"),
                ("Hotel Essentials", "Fresh Fruit", ""),
                # Health & Wellness
                ("Health", "Probiotics", "1 bottle"),
                ("Health", "Vitamins", "1 bottle"),
                ("Health", "Hand Sanitizer", "2 bottles"),
                ("Health", "Wet Wipes", "2 packs"),
                ("Health", "Tissues", "2 boxes"),
                ("Health", "Motion Sickness Medicine", "1 pack"),
                # Household
                ("Household", "Ziplock Bags", "1 box"),
                ("Household", "Plastic Utensils", "1 pack"),
                ("Household", "Napkins", "1 pack"),
            ]

            for category, item_name, quantity in international_items:
                GroceryListTemplateItem.objects.create(
                    template=international_template,
                    category=category,
                    item_name=item_name,
                    quantity=quantity,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created International Travel template with {len(international_items)} items"
                )
            )

        logger.info(
            "grocery_templates_seeded",
            template_count=GroceryListTemplate.objects.filter(is_system_template=True).count(),
        )

        self.stdout.write(
            self.style.SUCCESS("\n✓ All system grocery templates seeded successfully!")
        )
