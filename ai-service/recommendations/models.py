from django.db import models


class RecommendationRequest(models.Model):
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    strategy = models.CharField(max_length=64)
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["strategy", "created_at"]),
        ]

    def __str__(self):
        return f"RecommendationRequest {self.strategy} #{self.pk}"


class RecommendationResult(models.Model):
    request = models.ForeignKey(RecommendationRequest, on_delete=models.CASCADE, related_name="results")
    product_id = models.IntegerField(db_index=True)
    score = models.FloatField(default=0)
    deep_model_score = models.FloatField(null=True, blank=True)
    reason_codes = models.JSONField(default=list, blank=True)
    source_signals = models.JSONField(default=dict, blank=True)
    rank_position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank_position", "-score"]
        indexes = [
            models.Index(fields=["product_id", "score"]),
        ]

    def __str__(self):
        return f"RecommendationResult product={self.product_id} score={self.score}"


class ChatSession(models.Model):
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(fields=["user_id", "session_id"]),
        ]

    def __str__(self):
        return f"ChatSession user={self.user_id} session={self.session_id}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    message = models.TextField()
    retrieval_mode = models.CharField(max_length=64, blank=True)
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"ChatMessage {self.role} session={self.chat_session_id}"
