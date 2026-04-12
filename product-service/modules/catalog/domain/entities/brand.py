from dataclasses import dataclass


@dataclass(frozen=True)
class Brand:
    id: int | None
    name: str
    slug: str
