from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    id: int | None
    name: str
    slug: str
    parent_id: int | None = None
