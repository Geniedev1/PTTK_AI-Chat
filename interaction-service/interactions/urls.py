from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .graph_views import KnowledgeGraphViewSet
from .views import InteractionEventViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"events", InteractionEventViewSet, basename="interaction-event")
router.register(r"graph", KnowledgeGraphViewSet, basename="knowledge-graph")

urlpatterns = [
    path("", include(router.urls)),
]
