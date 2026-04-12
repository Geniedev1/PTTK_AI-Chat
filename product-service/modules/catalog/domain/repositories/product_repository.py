from abc import ABC, abstractmethod

from ..entities.product import Product
from ..entities.variant import Variant


class ProductRepository(ABC):
    @abstractmethod
    def create(self, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    def update(self, product_id: int, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, product_id: int) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def list(self, filters: dict[str, object] | None = None) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_variant(self, product_id: int, variant: Variant) -> Variant:
        raise NotImplementedError
