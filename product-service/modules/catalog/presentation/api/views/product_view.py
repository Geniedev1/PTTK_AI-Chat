from decimal import Decimal, InvalidOperation

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ....application.commands.create_product import CreateProductCommand
from ....application.commands.create_variant import CreateVariantCommand
from ....application.commands.update_product import UpdateProductCommand
from ....application.queries.filter_products import FilterProductsQuery
from ....application.queries.get_product import GetProductQuery
from ....application.queries.list_products import ListProductsQuery
from ....application.services.product_service import ProductApplicationService
from ....infrastructure.repositories.product_repository_impl import DjangoProductRepository
from ..permissions import CatalogWritePermission, has_catalog_admin_access
from ..serializers.product_serializer import ProductReadSerializer, ProductWriteSerializer, VariantSerializer
from ..tracking import emit_request_event


class ProductViewSet(viewsets.ViewSet):
    permission_classes = [CatalogWritePermission]
    repository_class = DjangoProductRepository
    service_class = ProductApplicationService

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = self.service_class(self.repository_class())

    def _serialize_product(self, product):
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "short_description": product.short_description,
            "description": product.description,
            "full_description": product.description,
            "category_id": product.category_id,
            "brand_id": product.brand_id,
            "product_type_id": product.product_type_id,
            "base_price": product.base_price,
            "stock": product.stock,
            "attributes": product.attributes.as_dict(),
            "is_active": product.is_active,
            "status": product.status(),
            "tags": product.tags,
            "image_urls": product.image_urls,
            "has_stock": product.has_stock(),
            "variants": [
                {
                    "id": variant.id,
                    "sku": variant.sku,
                    "name": variant.name,
                    "attributes": variant.attributes,
                    "stock": variant.stock,
                    "price_override": variant.price_override,
                    "is_default": variant.is_default,
                }
                for variant in product.variants
            ],
        }

    def _optional_int(self, value):
        return int(value) if value not in (None, "") else None

    def _optional_decimal(self, value):
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid decimal value: {value}") from exc

    def _build_filter_query(self, request):
        return FilterProductsQuery(
            category_id=self._optional_int(request.query_params.get("category_id")),
            product_type_id=self._optional_int(request.query_params.get("product_type_id")),
            brand_id=self._optional_int(request.query_params.get("brand_id")),
            in_stock=(request.query_params.get("in_stock") == "true") if "in_stock" in request.query_params else None,
            search=request.query_params.get("search"),
            min_price=self._optional_decimal(request.query_params.get("min_price")),
            max_price=self._optional_decimal(request.query_params.get("max_price")),
            sort_by=request.query_params.get("sort_by"),
            tag=request.query_params.get("tag"),
        )

    def list(self, request):
        has_filter_params = any(
            key in request.query_params
            for key in ["category_id", "product_type_id", "brand_id", "in_stock", "search", "min_price", "max_price", "sort_by", "tag"]
        )
        if has_filter_params:
            try:
                query = self._build_filter_query(request)
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            products = self.service.filter_products(query)
        else:
            include_inactive = (
                request.query_params.get("include_inactive") == "true" and has_catalog_admin_access(request)
            )
            products = self.service.list_products(ListProductsQuery(include_inactive=include_inactive))
        if request.query_params.get("search"):
            emit_request_event(
                request,
                event_type="search_performed",
                query_text=request.query_params.get("search"),
                metadata={
                    "result_count": len(products),
                    "product_ids": [product.id for product in products[:10]],
                    "filters": {key: request.query_params.get(key) for key in request.query_params},
                },
            )
        serializer = ProductReadSerializer([self._serialize_product(product) for product in products], many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        product = self.service.get_product(GetProductQuery(product_id=int(pk)))
        if not product or (not product.is_active and not has_catalog_admin_access(request)):
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        emit_request_event(
            request,
            event_type="product_viewed",
            product_id=product.id,
            metadata={
                "category_id": product.category_id,
                "brand_id": product.brand_id,
                "product_type_id": product.product_type_id,
                "referrer": request.query_params.get("referrer"),
            },
        )
        serializer = ProductReadSerializer(self._serialize_product(product))
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        try:
            query = self._build_filter_query(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        products = self.service.filter_products(query)
        emit_request_event(
            request,
            event_type="search_performed",
            query_text=request.query_params.get("search"),
            metadata={
                "result_count": len(products),
                "product_ids": [product.id for product in products[:10]],
                "filters": {key: request.query_params.get(key) for key in request.query_params},
            },
        )
        serializer = ProductReadSerializer([self._serialize_product(product) for product in products], many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.service.create_product(CreateProductCommand(**serializer.validated_data))
        return Response(ProductReadSerializer(self._serialize_product(product)).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = int(pk)
        if not self.service.get_product(GetProductQuery(product_id=product_id)):
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        product = self.service.update_product(product_id, UpdateProductCommand(**serializer.validated_data))
        return Response(ProductReadSerializer(self._serialize_product(product)).data)

    def destroy(self, request, pk=None):
        deleted = self.service.delete_product(int(pk))
        if not deleted:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def in_stock(self, request):
        products = self.service.filter_products(FilterProductsQuery(in_stock=True))
        serializer = ProductReadSerializer([self._serialize_product(product) for product in products], many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def variants(self, request, pk=None):
        serializer = VariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = int(pk)
        if not self.service.get_product(GetProductQuery(product_id=product_id)):
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        variant = self.service.create_variant(product_id, CreateVariantCommand(**serializer.validated_data))
        return Response(VariantSerializer(variant.__dict__).data, status=status.HTTP_201_CREATED)
