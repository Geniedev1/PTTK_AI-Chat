from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from ..infrastructure.models import ProductModel
from ..presentation.api.serializers.product_serializer import ProductWriteSerializer
from ..presentation.api.views.product_view import ProductViewSet


class ProductCatalogSerializerTest(TestCase):
    def test_full_description_is_mapped_to_description(self):
        serializer = ProductWriteSerializer(
            data={
                "name": "ThinkPad X1 Carbon",
                "short_description": "Ultrabook for business users.",
                "full_description": "Full length product description for search and AI.",
                "base_price": "1500.00",
                "tags": ["laptop", "business"],
                "image_urls": ["https://example.com/images/thinkpad-x1-carbon.jpg"],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["description"], "Full length product description for search and AI.")
        self.assertEqual(serializer.validated_data["tags"], ["laptop", "business"])


class ProductSearchViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ProductViewSet.as_view({"get": "search"})
        ProductModel.objects.create(
            name="MacBook Pro 14",
            short_description="Laptop for developer work, development, and video editing.",
            description="Apple laptop with M3 Pro chip for developers, coding, and creative work.",
            base_price=Decimal("2000.00"),
            stock=10,
            tags=["laptop", "apple", "developer"],
            image_urls=["https://example.com/images/macbook-pro-14.jpg"],
        )
        ProductModel.objects.create(
            name="Logitech G Pro X Headset",
            short_description="Gaming headset for esports voice chat.",
            description="Over-ear headset with Blue Voice microphone.",
            base_price=Decimal("129.00"),
            stock=20,
            tags=["headset", "gaming", "logitech"],
            image_urls=["https://example.com/images/logitech-g-pro-x.jpg"],
        )

    def test_search_matches_tags_and_descriptions(self):
        request = self.factory.get("/api/products/search/?search=developer")
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "MacBook Pro 14")

    def test_search_supports_price_sort(self):
        request = self.factory.get("/api/products/search/?sort_by=price_asc")
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Logitech G Pro X Headset")
        self.assertEqual(response.data[1]["name"], "MacBook Pro 14")
