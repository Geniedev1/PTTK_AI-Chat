from dataclasses import dataclass


@dataclass(frozen=True)
class Sku:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("SKU cannot be blank.")
