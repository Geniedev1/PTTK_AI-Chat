from ...domain.entities.product import Product
from ...domain.entities.variant import Variant
from ...domain.value_objects.attributes import Attributes
from ...domain.value_objects.sku import Sku
from ..commands.create_product import CreateProductCommand
from ..commands.create_variant import CreateVariantCommand
from ..commands.update_product import UpdateProductCommand
from ..queries.filter_products import FilterProductsQuery
from ..queries.get_product import GetProductQuery
from ..queries.list_products import ListProductsQuery


class ProductApplicationService:
    def __init__(self, repository):
        self.repository = repository

    def create_product(self, command: CreateProductCommand):
        entity = Product(
            id=None,
            name=command.name,
            description=command.description,
            category_id=command.category_id,
            brand_id=command.brand_id,
            product_type_id=command.product_type_id,
            base_price=command.base_price,
            stock=command.stock,
            attributes=Attributes(command.attributes),
            is_active=command.is_active,
        )
        return self.repository.create(entity)

    def update_product(self, product_id: int, command: UpdateProductCommand):
        entity = Product(
            id=product_id,
            name=command.name,
            description=command.description,
            category_id=command.category_id,
            brand_id=command.brand_id,
            product_type_id=command.product_type_id,
            base_price=command.base_price,
            stock=command.stock,
            attributes=Attributes(command.attributes),
            is_active=command.is_active,
        )
        return self.repository.update(product_id, entity)

    def get_product(self, query: GetProductQuery):
        return self.repository.get_by_id(query.product_id)

    def list_products(self, query: ListProductsQuery):
        return self.repository.list({"include_inactive": query.include_inactive})

    def filter_products(self, query: FilterProductsQuery):
        return self.repository.list(
            {
                "category_id": query.category_id,
                "product_type_id": query.product_type_id,
                "brand_id": query.brand_id,
                "in_stock": query.in_stock,
                "search": query.search,
            }
        )

    def delete_product(self, product_id: int):
        return self.repository.delete(product_id)

    def create_variant(self, product_id: int, command: CreateVariantCommand):
        entity = Variant(
            id=None,
            sku=Sku(command.sku).value,
            name=command.name,
            attributes=command.attributes,
            stock=command.stock,
            price_override=command.price_override,
            is_default=command.is_default,
        )
        return self.repository.create_variant(product_id, entity)
