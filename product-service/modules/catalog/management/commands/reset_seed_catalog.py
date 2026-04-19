from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from modules.catalog.models import BrandModel, CategoryModel, ProductModel, ProductTypeModel


CATALOG_PRODUCT_SEED = [
    {
        "name": "MacBook Air 13 M3",
        "short_description": "Lightweight laptop for coding, study, and office work.",
        "description": "Portable 13-inch laptop with strong battery life and smooth daily performance.",
        "category": "Laptops",
        "brand": "Apple",
        "product_type": "Laptop",
        "base_price": "1499.00",
        "stock": 14,
        "tags": ["laptop", "developer", "portable"],
        "attributes": {"cpu": "Apple M3", "ram": "16GB", "storage": "512GB"},
    },
    {
        "name": "Dell Inspiron 14 Plus",
        "short_description": "Balanced Windows laptop for productivity.",
        "description": "14-inch laptop for office, school, and daily multitasking.",
        "category": "Laptops",
        "brand": "Dell",
        "product_type": "Laptop",
        "base_price": "1099.00",
        "stock": 18,
        "tags": ["laptop", "windows", "office"],
        "attributes": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "1TB"},
    },
    {
        "name": "iPhone 15 128GB",
        "short_description": "Flagship smartphone with strong camera and smooth performance.",
        "description": "Great for social media, daily communication, and mobile photography.",
        "category": "Smartphones",
        "brand": "Apple",
        "product_type": "Phone",
        "base_price": "899.00",
        "stock": 22,
        "tags": ["phone", "ios", "camera"],
        "attributes": {"storage": "128GB", "network": "5G"},
    },
    {
        "name": "Samsung Galaxy S24 256GB",
        "short_description": "Premium Android phone for power users.",
        "description": "Fast Android phone with bright display and all-day battery.",
        "category": "Smartphones",
        "brand": "Samsung",
        "product_type": "Phone",
        "base_price": "999.00",
        "stock": 20,
        "tags": ["phone", "android", "premium"],
        "attributes": {"storage": "256GB", "network": "5G"},
    },
    {
        "name": "iPad Air 11 Wi-Fi",
        "short_description": "Tablet for note taking, sketching, and media consumption.",
        "description": "Light tablet for study and creative workflows.",
        "category": "Tablets",
        "brand": "Apple",
        "product_type": "Tablet",
        "base_price": "699.00",
        "stock": 16,
        "tags": ["tablet", "study", "creative"],
        "attributes": {"display": "11-inch", "storage": "128GB"},
    },
    {
        "name": "Samsung Galaxy Tab S9",
        "short_description": "High-refresh Android tablet for work and entertainment.",
        "description": "Versatile tablet for multitasking and media streaming.",
        "category": "Tablets",
        "brand": "Samsung",
        "product_type": "Tablet",
        "base_price": "749.00",
        "stock": 15,
        "tags": ["tablet", "android", "entertainment"],
        "attributes": {"display": "11-inch", "storage": "256GB"},
    },
    {
        "name": "Sony WH-1000XM5",
        "short_description": "Wireless noise-cancelling over-ear headphones.",
        "description": "Great for travel, focus work, and high quality music listening.",
        "category": "Audio",
        "brand": "Sony",
        "product_type": "Headphone",
        "base_price": "349.00",
        "stock": 24,
        "tags": ["audio", "anc", "wireless"],
        "attributes": {"type": "over-ear", "connectivity": "Bluetooth"},
    },
    {
        "name": "Jabra Elite 10",
        "short_description": "Premium true wireless earbuds with clear calls.",
        "description": "Comfortable earbuds for calls, gym, and commuting.",
        "category": "Audio",
        "brand": "Jabra",
        "product_type": "Earbuds",
        "base_price": "229.00",
        "stock": 26,
        "tags": ["audio", "earbuds", "wireless"],
        "attributes": {"type": "in-ear", "connectivity": "Bluetooth"},
    },
    {
        "name": "Canon EOS R50 Kit",
        "short_description": "Mirrorless camera for creators and beginners.",
        "description": "Compact camera with reliable autofocus for content and travel.",
        "category": "Cameras",
        "brand": "Canon",
        "product_type": "Camera",
        "base_price": "899.00",
        "stock": 12,
        "tags": ["camera", "creator", "mirrorless"],
        "attributes": {"sensor": "APS-C", "video": "4K"},
    },
    {
        "name": "Fujifilm X-S20 Body",
        "short_description": "Hybrid camera for photo and video creators.",
        "description": "Portable camera with strong image quality and film simulations.",
        "category": "Cameras",
        "brand": "Fujifilm",
        "product_type": "Camera",
        "base_price": "1299.00",
        "stock": 10,
        "tags": ["camera", "mirrorless", "video"],
        "attributes": {"sensor": "APS-C", "video": "6.2K"},
    },
    {
        "name": "LG UltraGear 27 QHD 165Hz",
        "short_description": "Gaming monitor with smooth motion and vivid colors.",
        "description": "27-inch QHD monitor for gaming and productivity.",
        "category": "Monitors",
        "brand": "LG",
        "product_type": "Monitor",
        "base_price": "329.00",
        "stock": 19,
        "tags": ["monitor", "gaming", "qhd"],
        "attributes": {"size": "27-inch", "refresh_rate": "165Hz"},
    },
    {
        "name": "Samsung Smart Monitor M8",
        "short_description": "All-in-one monitor for work and streaming.",
        "description": "32-inch monitor suitable for desk setup and home office.",
        "category": "Monitors",
        "brand": "Samsung",
        "product_type": "Monitor",
        "base_price": "519.00",
        "stock": 11,
        "tags": ["monitor", "smart", "office"],
        "attributes": {"size": "32-inch", "resolution": "4K"},
    },
    {
        "name": "Logitech MX Keys S",
        "short_description": "Quiet keyboard for office and coding setup.",
        "description": "Low-noise wireless keyboard for long typing sessions.",
        "category": "Peripherals",
        "brand": "Logitech",
        "product_type": "Keyboard",
        "base_price": "119.00",
        "stock": 30,
        "tags": ["keyboard", "wireless", "office"],
        "attributes": {"layout": "US", "connectivity": "Bluetooth"},
    },
    {
        "name": "Logitech MX Master 3S",
        "short_description": "Ergonomic productivity mouse.",
        "description": "Comfortable wireless mouse for creators and office users.",
        "category": "Peripherals",
        "brand": "Logitech",
        "product_type": "Mouse",
        "base_price": "109.00",
        "stock": 28,
        "tags": ["mouse", "ergonomic", "wireless"],
        "attributes": {"dpi": "8000", "connectivity": "Bluetooth"},
    },
    {
        "name": "Nike Pegasus 41",
        "short_description": "Daily running shoes for comfort and support.",
        "description": "Versatile running shoes for both training and walking.",
        "category": "Footwear",
        "brand": "Nike",
        "product_type": "Shoes",
        "base_price": "139.00",
        "stock": 25,
        "tags": ["shoes", "running", "sports"],
        "attributes": {"gender": "unisex", "material": "mesh"},
    },
    {
        "name": "Adidas Ultraboost Light",
        "short_description": "Cushioned sneakers for daily movement.",
        "description": "Comfort-focused shoes for running and all-day wear.",
        "category": "Footwear",
        "brand": "Adidas",
        "product_type": "Shoes",
        "base_price": "149.00",
        "stock": 21,
        "tags": ["shoes", "comfort", "sports"],
        "attributes": {"gender": "unisex", "material": "knit"},
    },
    {
        "name": "Uniqlo AIRism Tee",
        "short_description": "Breathable daily t-shirt.",
        "description": "Light shirt for hot weather and everyday outfit.",
        "category": "Apparel",
        "brand": "Uniqlo",
        "product_type": "Clothing",
        "base_price": "19.00",
        "stock": 40,
        "tags": ["clothing", "daily", "basic"],
        "attributes": {"type": "t-shirt", "material": "airism"},
    },
    {
        "name": "Levi 511 Slim Jeans",
        "short_description": "Classic slim-fit jeans.",
        "description": "Everyday denim that fits smart casual outfits.",
        "category": "Apparel",
        "brand": "Levi's",
        "product_type": "Clothing",
        "base_price": "79.00",
        "stock": 27,
        "tags": ["clothing", "jeans", "casual"],
        "attributes": {"type": "jeans", "fit": "slim"},
    },
    {
        "name": "Philips Air Fryer 6.2L",
        "short_description": "Large-capacity air fryer for family meals.",
        "description": "Healthy cooking appliance with fast hot-air circulation.",
        "category": "Home Appliances",
        "brand": "Philips",
        "product_type": "Appliance",
        "base_price": "169.00",
        "stock": 14,
        "tags": ["home", "kitchen", "appliance"],
        "attributes": {"capacity": "6.2L", "power": "2000W"},
    },
    {
        "name": "Xiaomi Robot Vacuum S10",
        "short_description": "Smart robot vacuum for daily floor cleaning.",
        "description": "Automatic vacuum and mop for apartment and home cleaning.",
        "category": "Home Appliances",
        "brand": "Xiaomi",
        "product_type": "Appliance",
        "base_price": "299.00",
        "stock": 13,
        "tags": ["home", "smart", "cleaning"],
        "attributes": {"suction": "4000Pa", "battery": "5200mAh"},
    },
    {
        "name": "Tefal Stainless Cookware Set",
        "short_description": "Durable cookware set for daily cooking.",
        "description": "Multi-piece cookware set for practical family kitchens.",
        "category": "Kitchenware",
        "brand": "Tefal",
        "product_type": "Kitchen",
        "base_price": "129.00",
        "stock": 17,
        "tags": ["kitchen", "cookware", "home"],
        "attributes": {"pieces": "7", "material": "stainless steel"},
    },
    {
        "name": "LocknLock Glass Container Set",
        "short_description": "Food storage containers with airtight lids.",
        "description": "Useful for meal prep and clean kitchen organization.",
        "category": "Kitchenware",
        "brand": "LocknLock",
        "product_type": "Kitchen",
        "base_price": "49.00",
        "stock": 29,
        "tags": ["kitchen", "storage", "meal-prep"],
        "attributes": {"pieces": "10", "material": "glass"},
    },
    {
        "name": "CeraVe Moisturizing Lotion",
        "short_description": "Daily hydration lotion for dry and sensitive skin.",
        "description": "Fragrance-free moisturizing lotion with ceramides.",
        "category": "Skincare",
        "brand": "CeraVe",
        "product_type": "Beauty",
        "base_price": "17.00",
        "stock": 33,
        "tags": ["beauty", "skincare", "daily"],
        "attributes": {"size": "473ml", "skin_type": "dry-sensitive"},
    },
    {
        "name": "La Roche-Posay SPF50",
        "short_description": "Lightweight sunscreen for daily UV protection.",
        "description": "Broad-spectrum sun protection for normal and sensitive skin.",
        "category": "Skincare",
        "brand": "La Roche-Posay",
        "product_type": "Beauty",
        "base_price": "24.00",
        "stock": 31,
        "tags": ["beauty", "sunscreen", "skincare"],
        "attributes": {"spf": "50+", "finish": "lightweight"},
    },
    {
        "name": "Decathlon Yoga Mat 8mm",
        "short_description": "Comfortable mat for yoga and stretching.",
        "description": "Cushioned yoga mat suitable for beginner and home workouts.",
        "category": "Fitness",
        "brand": "Decathlon",
        "product_type": "Sport",
        "base_price": "29.00",
        "stock": 26,
        "tags": ["fitness", "yoga", "home-workout"],
        "attributes": {"thickness": "8mm", "material": "TPE"},
    },
    {
        "name": "Xiaomi Smart Band 9",
        "short_description": "Fitness tracker for sleep and activity monitoring.",
        "description": "Affordable wearable to track daily movement and heart rate.",
        "category": "Fitness",
        "brand": "Xiaomi",
        "product_type": "Wearable",
        "base_price": "59.00",
        "stock": 35,
        "tags": ["fitness", "wearable", "health"],
        "attributes": {"battery": "21 days", "water_resistance": "5ATM"},
    },
    {
        "name": "Atomic Habits Paperback",
        "short_description": "Popular self-improvement book on habit building.",
        "description": "Practical framework for creating good habits and systems.",
        "category": "Books",
        "brand": "Penguin Random House",
        "product_type": "Book",
        "base_price": "16.00",
        "stock": 44,
        "tags": ["book", "self-help", "productivity"],
        "attributes": {"language": "English", "format": "paperback"},
    },
    {
        "name": "Deep Work Paperback",
        "short_description": "Productivity book about focused work.",
        "description": "Guidance on reducing distraction and improving concentration.",
        "category": "Books",
        "brand": "Grand Central",
        "product_type": "Book",
        "base_price": "15.00",
        "stock": 36,
        "tags": ["book", "focus", "productivity"],
        "attributes": {"language": "English", "format": "paperback"},
    },
    {
        "name": "LEGO Classic 10698",
        "short_description": "Creative building bricks for all ages.",
        "description": "Large box of bricks to build and play creatively.",
        "category": "Toys",
        "brand": "LEGO",
        "product_type": "Toy",
        "base_price": "42.00",
        "stock": 23,
        "tags": ["toy", "kids", "creative"],
        "attributes": {"pieces": "790", "age": "4+"},
    },
    {
        "name": "Rubik Cube 3x3 Speed",
        "short_description": "Smooth speed cube for puzzle practice.",
        "description": "Classic puzzle toy with smooth turning mechanism.",
        "category": "Toys",
        "brand": "Rubik's",
        "product_type": "Toy",
        "base_price": "12.00",
        "stock": 50,
        "tags": ["toy", "puzzle", "brain"],
        "attributes": {"size": "3x3", "material": "ABS"},
    },
    {
        "name": "Herschel Classic Backpack 24L",
        "short_description": "Daily backpack for school and commuting.",
        "description": "Simple and durable backpack with practical storage layout.",
        "category": "Bags",
        "brand": "Herschel",
        "product_type": "Bag",
        "base_price": "69.00",
        "stock": 22,
        "tags": ["bag", "daily", "commute"],
        "attributes": {"capacity": "24L", "material": "polyester"},
    },
    {
        "name": "Samsonite Cabin Spinner 20",
        "short_description": "Carry-on suitcase for short travel.",
        "description": "Compact luggage with smooth wheels and hard-shell protection.",
        "category": "Bags",
        "brand": "Samsonite",
        "product_type": "Luggage",
        "base_price": "139.00",
        "stock": 14,
        "tags": ["bag", "travel", "luggage"],
        "attributes": {"size": "20-inch", "material": "polycarbonate"},
    },
]


class Command(BaseCommand):
    help = "Delete existing catalog data and seed a fresh catalog of products with image URLs."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=30, help="Number of products to seed (max is available seed size).")
        parser.add_argument(
            "--skip-image-download",
            action="store_true",
            help="Skip downloading image files and only store image URLs in product records.",
        )
        parser.add_argument("--image-timeout", type=int, default=20, help="Timeout in seconds for each image download.")

    def handle(self, *args, **options):
        requested_count = max(1, int(options["count"]))
        product_rows = CATALOG_PRODUCT_SEED[:requested_count]
        if not product_rows:
            self.stdout.write(self.style.WARNING("No seed rows available."))
            return

        should_download_images = not options["skip_image_download"]
        image_timeout = max(5, int(options["image_timeout"]))
        image_dir = Path(settings.BASE_DIR) / "shared" / "seed-images"
        if should_download_images:
            image_dir.mkdir(parents=True, exist_ok=True)

        downloaded_images = 0
        failed_images = 0

        with transaction.atomic():
            deleted_products = ProductModel.objects.count()
            deleted_categories = CategoryModel.objects.count()
            deleted_brands = BrandModel.objects.count()
            deleted_product_types = ProductTypeModel.objects.count()

            ProductModel.objects.all().delete()
            CategoryModel.objects.all().delete()
            BrandModel.objects.all().delete()
            ProductTypeModel.objects.all().delete()

            category_map = {}
            brand_map = {}
            type_map = {}

            for row in product_rows:
                category = category_map.get(row["category"])
                if category is None:
                    category = CategoryModel.objects.create(name=row["category"])
                    category_map[row["category"]] = category

                brand = brand_map.get(row["brand"])
                if brand is None:
                    brand = BrandModel.objects.create(name=row["brand"])
                    brand_map[row["brand"]] = brand

                product_type = type_map.get(row["product_type"])
                if product_type is None:
                    type_code = slugify(row["product_type"])[:50] or "general"
                    product_type = ProductTypeModel.objects.create(
                        code=type_code,
                        name=row["product_type"],
                        description=f"Seed product type for {row['product_type']}.",
                    )
                    type_map[row["product_type"]] = product_type

                slug = slugify(row["name"]) or f"product-{len(category_map)}"
                image_url = f"https://picsum.photos/seed/{slug}/1200/900"

                if should_download_images:
                    target_file = image_dir / f"{slug}.jpg"
                    if self._download_image(image_url, target_file, timeout=image_timeout):
                        downloaded_images += 1
                    else:
                        failed_images += 1

                ProductModel.objects.create(
                    name=row["name"],
                    short_description=row["short_description"],
                    description=row["description"],
                    category=category,
                    brand=brand,
                    product_type=product_type,
                    base_price=row["base_price"],
                    stock=row["stock"],
                    attributes=row["attributes"],
                    tags=row["tags"],
                    image_urls=[image_url],
                    is_active=True,
                )

        self.stdout.write(self.style.SUCCESS("Catalog reset and reseed completed."))
        self.stdout.write(
            f"Deleted old rows: products={deleted_products}, categories={deleted_categories}, "
            f"brands={deleted_brands}, product_types={deleted_product_types}"
        )
        self.stdout.write(
            f"Seeded new rows: products={len(product_rows)}, categories={len(category_map)}, "
            f"brands={len(brand_map)}, product_types={len(type_map)}"
        )
        if should_download_images:
            self.stdout.write(
                f"Image downloads: success={downloaded_images}, failed={failed_images}, dir={image_dir}"
            )

    def _download_image(self, url, file_path, *, timeout):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException:
            return False

        file_path.write_bytes(response.content)
        return True
