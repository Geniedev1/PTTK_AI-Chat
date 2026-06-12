from django.contrib import admin

from .infrastructure.models import BrandModel, CategoryModel, ProductModel, ProductTypeModel, VariantModel


@admin.register(CategoryModel)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "parent")
    search_fields = ("name", "slug")


@admin.register(BrandModel)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")


@admin.register(ProductTypeModel)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    search_fields = ("code", "name")


class VariantInline(admin.TabularInline):
    model = VariantModel
    extra = 0


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "product_type", "category", "base_price", "stock", "is_active")
    list_filter = ("is_active", "product_type", "category", "brand")
    search_fields = ("name", "description")
    inlines = [VariantInline]
