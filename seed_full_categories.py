import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preloved.settings')
django.setup()

from ads.models import Category
from django.utils.text import slugify

CATEGORIES_DATA = [
    {
        "name": "Cars",
        "subcategories": [
            "Hatchback",
            "Sedan",
            "SUV",
            "MUV / Van",
            "Luxury Cars",
            "Electric Cars",
            "Car Spare Parts",
            "Car Accessories"
        ]
    },
    {
        "name": "Bikes",
        "subcategories": [
            "Motorcycles",
            "Scooters",
            "Bicycles",
            "Electric Bikes & Scooters",
            "Spare Parts",
            "Helmets & Riding Gear"
        ]
    },
    {
        "name": "Commercial Vehicles",
        "subcategories": [
            "Trucks",
            "Mini Trucks / Tempo",
            "Buses",
            "Auto Rickshaws / E-Rickshaws",
            "Tractors",
            "Spare Parts"
        ]
    },
    {
        "name": "Mobiles",
        "subcategories": [
            "Mobile Phones",
            "Tablets",
            "Smartwatches",
            "Accessories > (chargers, covers, earphones, power banks)"
        ]
    },
    {
        "name": "Electronics & Appliances",
        "subcategories": [
            "Laptops & Computers",
            "Computer Accessories > (keyboard, mouse, monitor)",
            "TVs",
            "Refrigerators",
            "Washing Machines",
            "Air Conditioners",
            "Coolers & Fans",
            "Kitchen Appliances > (mixer, microwave, induction)",
            "Cameras & Lenses",
            "Audio & Speakers",
            "Gaming Consoles & Games",
            "Printers & Scanners"
        ]
    },
    {
        "name": "Furniture & Home",
        "subcategories": [
            "Sofa & Dining Sets",
            "Beds & Mattresses",
            "Wardrobes & Cupboards",
            "Tables & Chairs",
            "Office Furniture",
            "Home Decor",
            "Kitchen & Utensils",
            "Garden & Outdoor"
        ]
    },
    {
        "name": "Fashion",
        "subcategories": [
            "Men's Clothing",
            "Women's Clothing",
            "Kids' Clothing",
            "Footwear",
            "Bags & Luggage",
            "Watches",
            "Jewellery",
            "Sunglasses & Accessories"
        ]
    },
    {
        "name": "Kids & Baby",
        "subcategories": [
            "Toys & Games",
            "Prams & Strollers",
            "Baby Cots & Furniture",
            "School Items",
            "Baby Care Items"
        ]
    },
    {
        "name": "Books, Sports & Hobbies",
        "subcategories": [
            "Books",
            "Study Material & Notes",
            "Gym & Fitness Equipment",
            "Cricket & Other Sports Gear",
            "Musical Instruments",
            "Art & Craft",
            "Collectibles & Antiques"
        ]
    },
    {
        "name": "Tools & Machinery",
        "subcategories": [
            "Hand Tools",
            "Power Tools",
            "Generators",
            "Industrial Machines",
            "Farm Equipment",
            "Construction Equipment"
        ]
    },
    {
        "name": "Properties",
        "subcategories": [
            "Houses & Apartments for Sale",
            "Houses & Apartments for Rent",
            "Land & Plots",
            "Shops & Offices",
            "PG / Hostels"
        ]
    },
    {
        "name": "Others",
        "subcategories": [
            "Anything else"
        ]
    }
]

def seed():
    print("Clearing old categories (including Services and Jobs)...")
    Category.objects.all().delete()

    total_main = 0
    total_sub = 0

    for cat_info in CATEGORIES_DATA:
        parent_name = cat_info["name"]
        parent_slug = slugify(parent_name)
        parent_cat = Category.objects.create(
            category_name=parent_name,
            slug=parent_slug,
            parent=None
        )
        total_main += 1
        print(f"[{total_main}] Created Main Category: {parent_name} (slug: {parent_slug})")

        for sub_name in cat_info["subcategories"]:
            sub_slug = f"{parent_slug}-{slugify(sub_name)[:80]}"
            # check uniqueness
            counter = 1
            final_sub_slug = sub_slug
            while Category.objects.filter(slug=final_sub_slug).exists():
                final_sub_slug = f"{sub_slug}-{counter}"
                counter += 1

            Category.objects.create(
                category_name=sub_name,
                slug=final_sub_slug,
                parent=parent_cat
            )
            total_sub += 1
            print(f"  └── Subcategory: {sub_name} (slug: {final_sub_slug})")

    print(f"\nSeeding complete! {total_main} Main Categories, {total_sub} Subcategories created.")

if __name__ == '__main__':
    seed()
