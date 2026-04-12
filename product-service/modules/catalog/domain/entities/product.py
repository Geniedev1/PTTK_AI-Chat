from dataclasses import dataclass, field
from decimal import Decimal

from ..value_objects.attributes import Attributes
from .variant import Variant


@dataclass(frozen=True)
class Product:
    id: int | None
    name: str
    description: str
    category_id: int | None
    brand_id: int | None
    product_type_id: int | None
    base_price: Decimal
    stock: int
    attributes: Attributes = field(default_factory=Attributes)
    is_active: bool = True
    variants: list[Variant] = field(default_factory=list)

    def has_stock(self) -> bool:
        return self.stock > 0 or any(variant.stock > 0 for variant in self.variants)
