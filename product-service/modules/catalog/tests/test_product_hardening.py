from decimal import Decimal

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from ..infrastructure.models import ProductModel
from ..presentation.api.serializers.product_serializer import ProductWriteSerializer
from ..presentation.api.views.product_view import ProductViewSet


class ProductWriteSerializerTest(TestCase):
    def test_rejects_negative_base_price(self):
        serializer = ProductWriteSerializer(
            data={
                "name": "Invalid product",
                "base_price": "-1.00",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("base_price", serializer.errors)


class ProductVisibilityTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ProductViewSet.as_view({"get": "retrieve"})
        self.product = ProductModel.objects.create(
            name="Hidden product",
            description="Should not be publicly visible",
            base_price=Decimal("100.00"),
            stock=5,
            is_active=False,
        )

    def test_inactive_product_is_hidden_from_public(self):
        request = self.factory.get(f"/api/products/{self.product.id}/")
        response = self.view(request, pk=self.product.id)

        self.assertEqual(response.status_code, 404)

    @override_settings(INTERNAL_ADMIN_KEY="secret")
    def test_inactive_product_is_visible_with_internal_admin_key(self):
        request = self.factory.get(
            f"/api/products/{self.product.id}/",
            HTTP_X_INTERNAL_ADMIN_KEY="secret",
        )
        response = self.view(request, pk=self.product.id)

        self.assertEqual(response.status_code, 200)
