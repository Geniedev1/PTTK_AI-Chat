from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .chat_views import ChatViewSet
from .views import RecommendationViewSet


router = DefaultRouter(trailing_slash=False)
router.register(r"recommend", RecommendationViewSet, basename="recommend")
router.register(r"chat", ChatViewSet, basename="chat")

urlpatterns = [
    path("", include(router.urls)),
]
