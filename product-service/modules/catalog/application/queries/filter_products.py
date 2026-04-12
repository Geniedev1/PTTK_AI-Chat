from dataclasses import dataclass


@dataclass(frozen=True)
class FilterProductsQuery:
    category_id: int | None = None
    product_type_id: int | None = None
    brand_id: int | None = None
    in_stock: bool | None = None
    search: str | None = None
