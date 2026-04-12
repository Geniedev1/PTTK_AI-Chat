from dataclasses import dataclass


@dataclass(frozen=True)
class GetProductQuery:
    product_id: int
