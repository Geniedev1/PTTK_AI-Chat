from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .chat_views import ChatViewSet
from .views import ModelStatusViewSet, ProfileViewSet, RecommendationViewSet


router = DefaultRouter(trailing_slash=False)
router.register(r"recommend", RecommendationViewSet, basename="recommend")
router.register(r"chat", ChatViewSet, basename="chat")
router.register(r"profile", ProfileViewSet, basename="profile")
router.register(r"models", ModelStatusViewSet, basename="models")

urlpatterns = [
    path("", include(router.urls)),
]
