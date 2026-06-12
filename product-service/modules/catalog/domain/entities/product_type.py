from dataclasses import dataclass


@dataclass(frozen=True)
class ProductType:
    id: int | None
    code: str
    name: str
    description: str = ""
