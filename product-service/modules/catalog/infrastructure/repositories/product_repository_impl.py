from ...domain.entities.product import Product
from ...domain.entities.variant import Variant
from ...domain.repositories.product_repository import ProductRepository
from ...domain.value_objects.attributes import Attributes
from ..models import ProductModel, VariantModel


class DjangoProductRepository(ProductRepository):
    def _to_entity(self, instance: ProductModel) -> Product:
        variants = [
            Variant(
                id=variant.id,
                sku=variant.sku,
                name=variant.name,
                attributes=variant.attributes or {},
                stock=variant.stock,
                price_override=variant.price_override,
                is_default=variant.is_default,
            )
            for variant in instance.variants.all()
        ]
        return Product(
            id=instance.id,
            name=instance.name,
            slug=instance.slug,
            short_description=instance.short_description,
            description=instance.description,
            category_id=instance.category_id,
            brand_id=instance.brand_id,
            product_type_id=instance.product_type_id,
            base_price=instance.base_price,
            stock=instance.stock,
            attributes=Attributes(instance.attributes or {}),
            is_active=instance.is_active,
            tags=list(instance.tags or []),
            image_urls=list(instance.image_urls or []),
            variants=variants,
        )

    def create(self, product: Product) -> Product:
        instance = ProductModel.objects.create(
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            description=product.description,
            category_id=product.category_id,
            brand_id=product.brand_id,
            product_type_id=product.product_type_id,
            base_price=product.base_price,
            stock=product.stock,
            attributes=product.attributes.as_dict(),
            tags=product.tags,
            image_urls=product.image_urls,
            is_active=product.is_active,
        )
        return self._to_entity(instance)

    def update(self, product_id: int, product: Product) -> Product:
        instance = ProductModel.objects.get(pk=product_id)
        instance.name = product.name
        instance.slug = product.slug
        instance.short_description = product.short_description
        instance.description = product.description
        instance.category_id = product.category_id
        instance.brand_id = product.brand_id
        instance.product_type_id = product.product_type_id
        instance.base_price = product.base_price
        instance.stock = product.stock
        instance.attributes = product.attributes.as_dict()
        instance.tags = product.tags
        instance.image_urls = product.image_urls
        instance.is_active = product.is_active
        instance.save()
        instance.refresh_from_db()
        return self._to_entity(instance)

    def get_by_id(self, product_id: int) -> Product | None:
        instance = ProductModel.objects.filter(pk=product_id).prefetch_related("variants").first()
        if not instance:
            return None
        return self._to_entity(instance)

    def list(self, filters: dict[str, object] | None = None) -> list[Product]:
        queryset = ProductModel.objects.prefetch_related("variants").all()
        filters = filters or {}

        if not filters.get("include_inactive"):
            queryset = queryset.active()
        if filters.get("category_id"):
            queryset = queryset.by_category(filters["category_id"])
        if filters.get("product_type_id"):
            queryset = queryset.by_product_type(filters["product_type_id"])
        if filters.get("brand_id"):
            queryset = queryset.filter(brand_id=filters["brand_id"])
        if filters.get("in_stock") is True:
            queryset = queryset.in_stock()
        if filters.get("min_price") is not None:
            queryset = queryset.filter(base_price__gte=filters["min_price"])
        if filters.get("max_price") is not None:
            queryset = queryset.filter(base_price__lte=filters["max_price"])
        if filters.get("tag"):
            queryset = queryset.filter(tags__icontains=filters["tag"])
        if filters.get("search"):
            search = filters["search"]
            queryset = queryset.filter_search(search)

        sort_by = filters.get("sort_by") or "newest"
        queryset = queryset.sort_by_option(sort_by)

        return [self._to_entity(instance) for instance in queryset]

    def delete(self, product_id: int) -> bool:
        deleted, _ = ProductModel.objects.filter(pk=product_id).delete()
        return deleted > 0

    def create_variant(self, product_id: int, variant: Variant) -> Variant:
        instance = VariantModel.objects.create(
            product_id=product_id,
            sku=variant.sku,
            name=variant.name,
            attributes=variant.attributes,
            stock=variant.stock,
            price_override=variant.price_override,
            is_default=variant.is_default,
        )
        return Variant(
            id=instance.id,
            sku=instance.sku,
            name=instance.name,
            attributes=instance.attributes or {},
            stock=instance.stock,
            price_override=instance.price_override,
            is_default=instance.is_default,
        )
