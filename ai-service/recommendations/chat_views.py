import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .chat_serializers import ChatRequestSerializer, ChatRetrieveRequestSerializer
from .chat_services import ChatbotService, ServiceClientError


logger = logging.getLogger(__name__)


class ChatViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    service_class = ChatbotService

    def create(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        try:
            payload = self.service_class().chat(**validated)
        except ServiceClientError as exc:
            return Response({"detail": str(exc)}, status=exc.status_code or status.HTTP_502_BAD_GATEWAY)
        logger.info(
            "ai_chat_result request_id=%s user_id=%s session_id=%s used_realtime_api=%s used_graph_context=%s retrieval_mode=%s source_ids=%s",
            getattr(request, "request_id", "-"),
            validated.get("user_id"),
            validated.get("session_id"),
            payload.get("used_realtime_api"),
            payload.get("used_graph_context"),
            payload.get("retrieval_mode"),
            [source.get("source_id") for source in payload.get("sources", [])[:5]],
        )
        return Response(payload)

    @action(detail=False, methods=["post"], url_path="retrieve")
    def retrieve_context(self, request):
        serializer = ChatRetrieveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        limit = validated.pop("limit", 5)
        try:
            payload = self.service_class().retrieve(limit=limit, **validated)
        except ServiceClientError as exc:
            return Response({"detail": str(exc)}, status=exc.status_code or status.HTTP_502_BAD_GATEWAY)
        logger.info(
            "ai_chat_retrieve request_id=%s user_id=%s session_id=%s retrieval_mode=%s source_ids=%s profile_snapshot=%s",
            getattr(request, "request_id", "-"),
            validated.get("user_id"),
            validated.get("session_id"),
            payload.get("retrieval_mode"),
            [source.get("source_id") for source in payload.get("sources", [])[:5]],
            payload.get("profile_snapshot"),
        )
        return Response(payload)
