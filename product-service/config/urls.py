from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/products/", include("modules.catalog.presentation.api.urls")),
]
