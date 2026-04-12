from django.db import models


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def in_stock(self):
        return self.filter(stock__gt=0)

    def by_category(self, category_id: int):
        return self.filter(category_id=category_id)

    def by_product_type(self, product_type_id: int):
        return self.filter(product_type_id=product_type_id)
