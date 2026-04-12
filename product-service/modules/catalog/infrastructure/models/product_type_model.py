from django.db import models


class ProductTypeModel(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "catalog_product_types"
        ordering = ["name"]

    def __str__(self):
        return self.name
