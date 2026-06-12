from dataclasses import dataclass


@dataclass(frozen=True)
class ListProductsQuery:
    include_inactive: bool = False
