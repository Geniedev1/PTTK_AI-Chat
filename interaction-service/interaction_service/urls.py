from django.urls import include, path

urlpatterns = [
    path("api/interactions/", include("interactions.urls")),
]
