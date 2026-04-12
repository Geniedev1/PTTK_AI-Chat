from django.db import models

from ..querysets.product_queryset import ProductQuerySet


class ProductModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey("catalog.CategoryModel", null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    brand = models.ForeignKey("catalog.BrandModel", null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    product_type = models.ForeignKey(
        "catalog.ProductTypeModel",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        db_table = "catalog_products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
