from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    description: str = ""
    category_id: int | None = None
    brand_id: int | None = None
    product_type_id: int | None = None
    base_price: Decimal = Decimal("0")
    stock: int = 0
    attributes: dict[str, object] = field(default_factory=dict)
    is_active: bool = True
