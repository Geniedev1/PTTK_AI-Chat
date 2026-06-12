from django.db import models


class VariantModel(models.Model):
    product = models.ForeignKey("catalog.ProductModel", on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    attributes = models.JSONField(default=dict, blank=True)
    stock = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_variants"
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_id}:{self.sku}"
