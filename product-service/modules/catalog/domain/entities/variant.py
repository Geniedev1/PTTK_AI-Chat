from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Variant:
    id: int | None
    sku: str
    name: str
    attributes: dict[str, object] = field(default_factory=dict)
    stock: int = 0
    price_override: Decimal | None = None
    is_default: bool = False
