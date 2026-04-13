from django.db import models
from django.utils.text import slugify

from ..querysets.product_queryset import ProductQuerySet


class ProductModel(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    short_description = models.TextField(blank=True)
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
    tags = models.JSONField(default=list, blank=True)
    image_urls = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        db_table = "catalog_products"
        ordering = ["-created_at"]

    def _generate_unique_slug(self):
        base_slug = slugify(self.slug or self.name) or "product"
        slug = base_slug
        suffix = 2

        while ProductModel.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return slug

    def save(self, *args, **kwargs):
        self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
