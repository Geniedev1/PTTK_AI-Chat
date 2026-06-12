from django.db import models
from django.db.models import Q


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def in_stock(self):
        return self.filter(Q(stock__gt=0) | Q(variants__stock__gt=0)).distinct()

    def by_category(self, category_id: int):
        return self.filter(category_id=category_id)

    def by_product_type(self, product_type_id: int):
        return self.filter(product_type_id=product_type_id)

    def filter_search(self, search: str):
        return self.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(short_description__icontains=search)
            | Q(description__icontains=search)
            | Q(tags__icontains=search)
            | Q(category__name__icontains=search)
            | Q(brand__name__icontains=search)
        ).distinct()

    def sort_by_option(self, sort_by: str):
        mapping = {
            "newest": ("-created_at",),
            "oldest": ("created_at",),
            "price_asc": ("base_price", "-created_at"),
            "price_desc": ("-base_price", "-created_at"),
            "name_asc": ("name",),
            "name_desc": ("-name",),
        }
        ordering = mapping.get(sort_by, mapping["newest"])
        return self.order_by(*ordering)
