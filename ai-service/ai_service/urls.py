from django.urls import include, path


urlpatterns = [
    path("api/ai/", include("recommendations.urls")),
]
