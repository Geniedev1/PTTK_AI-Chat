import json
import logging
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests
from django.conf import settings

from .profile_utils import BehavioralProfileBuilder
from .services import ProductCatalogClient, ServiceClientError


logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
CART_KEYWORDS = ("cart", "gio hang", "basket", "checkout")
PRICE_KEYWORDS = ("price", "gia", "bao nhieu")
STOCK_KEYWORDS = ("stock", "ton kho", "con hang", "available")
ORDER_STATUS_TERMS = ("status", "trang thai", "pending", "confirmed", "paid", "completed", "cancelled", "my order", "where is")
GREETING_KEYWORDS = ("xin chao", "chao", "hello", "hi", "hey")
DOMAIN_INTENT_KEYWORDS = (
    "product",
    "san pham",
    "gia",
    "price",
    "stock",
    "ton kho",
    "order",
    "don hang",
    "cart",
    "gio hang",
    "shipping",
    "payment",
    "return",
    "policy",
    "faq",
)
CAPABILITY_QUESTION_KEYWORDS = (
    "ban co the lam gi",
    "ban lam duoc gi",
    "what can you do",
    "what do you do",
    "help me",
)
ADVICE_KEYWORDS = (
    "tu van",
    "goi y",
    "de xuat",
    "recommend",
    "suggest",
)


@dataclass
class KnowledgeChunk:
    source_type: str
    source_id: str
    title: str
    text: str
    product_id: int | None = None
    category_id: int | None = None
    brand_id: int | None = None


class OrderClient:
    def __init__(self):
        self.base_url = getattr(settings, "ORDER_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def fetch_order(self, *, order_id=None, customer_id=None, session_id=None):
        if not self.base_url:
            raise ServiceClientError("ORDER_SERVICE_URL is not configured.")

        headers = {}
        params = {}
        if session_id:
            headers["X-Cart-Session-Key"] = str(session_id)
        if customer_id is not None:
            params["customer_id"] = int(customer_id)

        try:
            if order_id is not None:
                response = requests.get(
                    f"{self.base_url}/api/orders/{int(order_id)}",
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
            else:
                response = requests.get(
                    f"{self.base_url}/api/orders/",
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
        except requests.RequestException as exc:
            raise ServiceClientError(f"Order service request failed: {exc}") from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise ServiceClientError("Order service returned an error.", status_code=response.status_code)

        payload = response.json()
        if order_id is not None:
            return payload
        if isinstance(payload, list) and payload:
            return payload[0]
        return None


class CartStatusClient:
    def __init__(self):
        self.base_url = getattr(settings, "CART_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def fetch_current_cart(self, session_id):
        if not self.base_url:
            raise ServiceClientError("CART_SERVICE_URL is not configured.")
        try:
            response = requests.get(
                f"{self.base_url}/api/cart/current",
                headers={"X-Cart-Session-Key": str(session_id)},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceClientError(f"Cart service request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ServiceClientError("Cart service returned an error.", status_code=response.status_code)
        return response.json()


class InteractionContextClient:
    def __init__(self):
        self.base_url = getattr(settings, "INTERACTION_SERVICE_URL", "").rstrip("/")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    def _get_optional(self, path, params=None):
        if not self.base_url:
            return []
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                params=params or {},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Interaction context request failed for %s: %s", path, exc)
            return []
        return response.json()

    def emit_chat_event(self, *, event_type, message, user_id=None, session_id=None, metadata=None):
        if not self.base_url:
            return False
        payload = {
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id,
            "query_text": message[:500],
            "source": "ai-service",
            "metadata": metadata or {},
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/interactions/events",
                json=payload,
                timeout=self.timeout,
            )
            return response.status_code == 201
        except requests.RequestException:
            return False

    def fetch_user_interest(self, *, user_id=None, session_id=None, limit=3):
        params = {"limit": limit}
        if user_id is not None:
            params["user_id"] = int(user_id)
        elif session_id:
            params["session_id"] = session_id
        else:
            return []
        return self._get_optional("/api/interactions/graph/user_interest", params=params)

    def fetch_query_paths(self, *, query_text, limit=3):
        if not query_text:
            return []
        return self._get_optional(
            "/api/interactions/graph/query_paths",
            params={"query_text": query_text, "limit": limit},
        )

    def fetch_events(self, *, user_id=None, session_id=None, limit=20):
        params = {"limit": limit}
        if user_id is not None:
            params["user_id"] = int(user_id)
        elif session_id:
            params["session_id"] = session_id
        else:
            return []
        return self._get_optional("/api/interactions/events", params=params)


class OpenAIClient:
    def __init__(self):
        self.base_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.chat_model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.embedding_model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.timeout = getattr(settings, "REQUEST_TIMEOUT_SECONDS", 10)

    @property
    def enabled(self):
        return bool(self.api_key)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_answer(self, *, prompt, question):
        if not self.enabled:
            return None
        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("OpenAI chat/completions request failed: %s", exc)
            return None

        data = response.json()
        # Chat Completions API: choices[0].message.content
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
            return content.strip() or None
        return None

    def embed_texts(self, texts):
        if not self.enabled or not getattr(settings, "OPENAI_ENABLE_EMBEDDINGS", True) or not texts:
            return None
        payload = {
            "model": self.embedding_model,
            "input": texts,
        }
        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("OpenAI embedding request failed: %s", exc)
            return None
        data = response.json()
        return [row.get("embedding", []) for row in data.get("data", [])]


class ChatbotService:
    def __init__(
        self,
        product_client=None,
        order_client=None,
        cart_client=None,
        interaction_client=None,
        openai_client=None,
        profile_builder=None,
    ):
        self.product_client = product_client or ProductCatalogClient()
        self.order_client = order_client or OrderClient()
        self.cart_client = cart_client or CartStatusClient()
        self.interaction_client = interaction_client or InteractionContextClient()
        self.openai_client = openai_client or OpenAIClient()
        self.profile_builder = profile_builder or BehavioralProfileBuilder(
            interaction_client=self.interaction_client,
            cart_client=self.cart_client,
        )

    def chat(self, *, message, user_id=None, session_id=None, customer_id=None, product_id=None, order_id=None):
        normalized_message = message.strip()
        self._emit_chat_lifecycle_events(
            message=normalized_message,
            user_id=user_id,
            session_id=session_id,
            customer_id=customer_id,
            product_id=product_id,
            order_id=order_id,
        )

        realtime = self._route_realtime(
            normalized_message,
            user_id=user_id,
            session_id=session_id,
            customer_id=customer_id,
            product_id=product_id,
            order_id=order_id,
        )
        if realtime is not None:
            return realtime

        if self._is_greeting_message(normalized_message):
            profile_snapshot = self._build_profile_snapshot({}, user_id=user_id, session_id=session_id)
            return {
                "answer": self._generate_greeting_answer(
                    normalized_message,
                    profile_snapshot=profile_snapshot,
                    user_id=user_id,
                    session_id=session_id,
                ),
                "sources": [],
                "used_realtime_api": False,
                "used_graph_context": False,
                "retrieval_mode": "greeting",
                "profile_snapshot": profile_snapshot,
            }

        retrieval = self.retrieve(
            message=normalized_message,
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            limit=getattr(settings, "CHAT_RETRIEVAL_LIMIT", 5),
        )

        if self._should_use_general_answer(normalized_message, retrieval):
            general_answer = self._generate_general_answer(
                normalized_message,
                user_id=user_id,
                session_id=session_id,
            )
            if general_answer:
                return {
                    "answer": general_answer,
                    "sources": [],
                    "used_realtime_api": False,
                    "used_graph_context": False,
                    "retrieval_mode": "general-openai",
                    "profile_snapshot": retrieval["profile_snapshot"],
                }
            return {
                "answer": self._general_fallback_answer(),
                "sources": [],
                "used_realtime_api": False,
                "used_graph_context": False,
                "retrieval_mode": "general-fallback",
                "profile_snapshot": retrieval["profile_snapshot"],
            }

        answer = self._generate_grounded_answer(
            normalized_message,
            retrieval,
            user_id=user_id,
            session_id=session_id,
        )
        return {
            "answer": answer,
            "sources": retrieval["sources"],
            "used_realtime_api": False,
            "used_graph_context": retrieval["used_graph_context"],
            "retrieval_mode": retrieval["retrieval_mode"],
            "profile_snapshot": retrieval["profile_snapshot"],
        }

    def _emit_chat_lifecycle_events(self, *, message, user_id=None, session_id=None, customer_id=None, product_id=None, order_id=None):
        # Interaction service requires at least one identity scope.
        if user_id is None and not session_id:
            return

        metadata = {"customer_id": customer_id, "product_id": product_id, "order_id": order_id}
        history = self.interaction_client.fetch_events(user_id=user_id, session_id=session_id, limit=20)
        has_chat_history = any(
            row.get("event_type") in {"chat_started", "chat_message_sent"}
            for row in history
        )
        if not has_chat_history:
            self.interaction_client.emit_chat_event(
                event_type="chat_started",
                message=message,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
            )

        self.interaction_client.emit_chat_event(
            event_type="chat_message_sent",
            message=message,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
        )

    def retrieve(self, *, message, user_id=None, session_id=None, product_id=None, limit=5):
        products = self.product_client.fetch_products()
        product_lookup = {
            int(product["id"]): product
            for product in products
            if product.get("is_active", False)
        }
        profile_snapshot = self._build_profile_snapshot(product_lookup, user_id=user_id, session_id=session_id)
        chunks = self._build_chunks(products)
        selected_chunks, retrieval_mode = self._select_chunks(
            message=message,
            chunks=chunks,
            product_id=product_id,
            profile_snapshot=profile_snapshot,
            limit=limit,
        )
        graph_context = self._build_graph_context(message=message, user_id=user_id, session_id=session_id)
        return {
            "query": message,
            "sources": [self._chunk_to_source(chunk, score) for chunk, score in selected_chunks],
            "graph_context": graph_context,
            "used_graph_context": bool(graph_context),
            "retrieval_mode": retrieval_mode,
            "profile_snapshot": profile_snapshot,
        }

    def _route_realtime(self, message, *, user_id=None, session_id=None, customer_id=None, product_id=None, order_id=None):
        lowered = self._normalize_text(message)
        if self._is_order_status_question(lowered, order_id=order_id):
            return self._answer_order_status(
                message=message,
                user_id=user_id,
                customer_id=customer_id,
                session_id=session_id,
                order_id=order_id,
            )
        if self._contains_any(lowered, CART_KEYWORDS):
            return self._answer_cart_status(message=message, user_id=user_id, session_id=session_id)
        if self._contains_any(lowered, PRICE_KEYWORDS) or self._contains_any(lowered, STOCK_KEYWORDS):
            return self._answer_product_runtime(
                message,
                user_id=user_id,
                session_id=session_id,
                product_id=product_id,
            )
        return None

    def _answer_order_status(self, message, *, user_id=None, customer_id=None, session_id=None, order_id=None):
        order = self.order_client.fetch_order(order_id=order_id, customer_id=customer_id, session_id=session_id)
        if not order:
            answer = "I could not find an order in the current scope. Provide `order_id`, or send `customer_id` or `session_id` so I can check the latest order."
            return {
                "answer": answer,
                "sources": [],
                "used_realtime_api": True,
                "used_graph_context": False,
                "retrieval_mode": "realtime-order",
            }

        order_identifier = order.get("id")
        status_text = order.get("status", "UNKNOWN")
        total_amount = order.get("total_amount")
        item_count = len(order.get("items", []))
        answer = f"Order #{order_identifier} is currently `{status_text}`. Total amount is {total_amount} with {item_count} item(s)."
        facts = {
            "order_id": order_identifier,
            "status": status_text,
            "total_amount": total_amount,
            "item_count": item_count,
        }
        return {
            "answer": self._naturalize_realtime_answer(
                message=message,
                fallback_answer=answer,
                facts=facts,
                scope_label="order status",
                user_id=user_id,
                session_id=session_id,
            ),
            "sources": [
                {
                    "source_type": "realtime_order",
                    "source_id": str(order_identifier),
                    "title": f"Order #{order_identifier}",
                    "excerpt": json.dumps({"status": status_text, "total_amount": total_amount}),
                }
            ],
            "used_realtime_api": True,
            "used_graph_context": False,
            "retrieval_mode": "realtime-order",
        }

    def _answer_cart_status(self, message, *, user_id=None, session_id=None):
        if not session_id:
            return {
                "answer": "I need `session_id` to inspect the current cart.",
                "sources": [],
                "used_realtime_api": True,
                "used_graph_context": False,
                "retrieval_mode": "realtime-cart",
            }

        cart = self.cart_client.fetch_current_cart(session_id)
        answer = (
            f"Current cart has {cart.get('item_count', 0)} line item(s), "
            f"{cart.get('total_quantity', 0)} total unit(s), "
            f"and subtotal {cart.get('subtotal_amount', '0.00')}."
        )
        facts = {
            "session_id": session_id,
            "item_count": cart.get("item_count", 0),
            "total_quantity": cart.get("total_quantity", 0),
            "subtotal_amount": cart.get("subtotal_amount", "0.00"),
        }
        return {
            "answer": self._naturalize_realtime_answer(
                message=message,
                fallback_answer=answer,
                facts=facts,
                scope_label="cart summary",
                user_id=user_id,
                session_id=session_id,
            ),
            "sources": [
                {
                    "source_type": "realtime_cart",
                    "source_id": session_id,
                    "title": f"Cart {session_id}",
                    "excerpt": json.dumps(
                        {
                            "item_count": cart.get("item_count", 0),
                            "total_quantity": cart.get("total_quantity", 0),
                            "subtotal_amount": cart.get("subtotal_amount", "0.00"),
                        }
                    ),
                }
            ],
            "used_realtime_api": True,
            "used_graph_context": False,
            "retrieval_mode": "realtime-cart",
        }

    def _answer_product_runtime(self, message, *, user_id=None, session_id=None, product_id=None):
        products = self.product_client.fetch_products()
        product = self._resolve_product(products, explicit_product_id=product_id, message=message)
        if not product:
            return {
                "answer": "I need a `product_id` or a clearer product name to verify current price or stock.",
                "sources": [],
                "used_realtime_api": True,
                "used_graph_context": False,
                "retrieval_mode": "realtime-product",
            }

        product_id = int(product["id"])
        runtime_product = self.product_client.fetch_product(product_id)
        wants_price = self._contains_any(message, PRICE_KEYWORDS)
        wants_stock = self._contains_any(message, STOCK_KEYWORDS)

        segments = [f"Product `{runtime_product.get('name')}`"]
        if wants_price or not wants_stock:
            segments.append(f"current price is {runtime_product.get('base_price')}")
        if wants_stock or not wants_price:
            in_stock = "in stock" if runtime_product.get("has_stock") else "currently out of stock"
            segments.append(in_stock)
        answer = ", ".join(segments) + "."
        facts = {
            "product_id": product_id,
            "product_name": runtime_product.get("name"),
            "base_price": runtime_product.get("base_price"),
            "stock": runtime_product.get("stock"),
            "has_stock": runtime_product.get("has_stock"),
            "user_asked_price": wants_price,
            "user_asked_stock": wants_stock,
        }

        return {
            "answer": self._naturalize_realtime_answer(
                message=message,
                fallback_answer=answer,
                facts=facts,
                scope_label="product runtime lookup",
                user_id=user_id,
                session_id=session_id,
            ),
            "sources": [
                {
                    "source_type": "realtime_product",
                    "source_id": str(product_id),
                    "title": runtime_product.get("name") or f"Product {product_id}",
                    "excerpt": json.dumps(
                        {
                            "base_price": runtime_product.get("base_price"),
                            "stock": runtime_product.get("stock"),
                            "has_stock": runtime_product.get("has_stock"),
                        }
                    ),
                }
            ],
            "used_realtime_api": True,
            "used_graph_context": False,
            "retrieval_mode": "realtime-product",
        }

    def _build_chunks(self, products):
        chunks = []
        for product in products:
            if not product.get("is_active", False):
                continue
            product_text = self._product_text(product)
            chunks.append(
                KnowledgeChunk(
                    source_type="product",
                    source_id=str(product["id"]),
                    title=product.get("name") or f"Product {product['id']}",
                    text=product_text,
                    product_id=int(product["id"]),
                    category_id=product.get("category_id"),
                    brand_id=product.get("brand_id"),
                )
            )

        knowledge_dir = Path(getattr(settings, "KNOWLEDGE_BASE_DIR"))
        for policy_path in sorted((knowledge_dir / "policies").glob("*.md")):
            text = policy_path.read_text(encoding="utf-8")
            for index, chunk_text in enumerate(self._split_text(text), start=1):
                chunks.append(
                    KnowledgeChunk(
                        source_type="policy",
                        source_id=f"{policy_path.stem}-{index}",
                        title=policy_path.stem.replace("-", " ").title(),
                        text=chunk_text,
                    )
                )
        return chunks

    def _select_chunks(self, *, message, chunks, product_id=None, profile_snapshot=None, limit=5):
        if not chunks:
            return [], "empty"

        query_text = message.strip()
        embedding_scores = self._rank_chunks_by_embedding(query_text, chunks)
        if embedding_scores:
            ranked = self._apply_profile_bias_to_ranked_chunks(embedding_scores, profile_snapshot)
            mode = "embedding"
        else:
            ranked = self._rank_chunks_lexically(
                query_text,
                chunks,
                product_id=product_id,
                profile_snapshot=profile_snapshot,
            )
            mode = "lexical"
        return ranked[:limit], mode

    def _rank_chunks_by_embedding(self, query_text, chunks):
        payload = [query_text] + [chunk.text for chunk in chunks]
        embeddings = self.openai_client.embed_texts(payload)
        if not embeddings or len(embeddings) != len(payload):
            return None
        query_embedding = embeddings[0]
        ranked = []
        for chunk, chunk_embedding in zip(chunks, embeddings[1:]):
            score = self._cosine_similarity(query_embedding, chunk_embedding)
            if score > 0:
                ranked.append((chunk, score))
        ranked.sort(key=lambda item: (-item[1], item[0].source_type, item[0].source_id))
        return ranked

    def _rank_chunks_lexically(self, query_text, chunks, *, product_id=None, profile_snapshot=None):
        query_tokens = self._tokens(query_text)
        ranked = []
        for chunk in chunks:
            text_tokens = self._tokens(chunk.text)
            overlap = len(query_tokens & text_tokens)
            score = float(overlap)
            if product_id is not None and chunk.product_id == int(product_id):
                score += 3.0
            if any(token in (chunk.title or "").lower() for token in query_tokens):
                score += 1.0
            if chunk.source_type == "policy" and any(token in chunk.text.lower() for token in query_tokens):
                score += 0.5
            score += self._profile_bias(chunk, profile_snapshot or {})
            if score > 0:
                ranked.append((chunk, score))

        ranked.sort(key=lambda item: (-item[1], item[0].source_type, item[0].source_id))
        return ranked

    def _apply_profile_bias_to_ranked_chunks(self, ranked_chunks, profile_snapshot):
        adjusted = []
        for chunk, score in ranked_chunks:
            adjusted.append((chunk, score + self._profile_bias(chunk, profile_snapshot or {})))
        adjusted.sort(key=lambda item: (-item[1], item[0].source_type, item[0].source_id))
        return adjusted

    def _build_graph_context(self, *, message, user_id=None, session_id=None):
        context = []
        for row in self.interaction_client.fetch_user_interest(user_id=user_id, session_id=session_id, limit=2):
            context.append(
                {
                    "type": "user_interest",
                    "label": row.get("category_name") or f"Category {row.get('category_id')}",
                    "score": row.get("total_weight", 0),
                }
            )
        for row in self.interaction_client.fetch_query_paths(query_text=message, limit=2):
            context.append(
                {
                    "type": "query_path",
                    "label": row.get("product_name") or f"Product {row.get('product_id')}",
                    "score": row.get("total_weight", 0),
                }
            )
        return context[:4]

    def _build_profile_snapshot(self, products, *, user_id=None, session_id=None):
        return self.profile_builder.build(products, user_id=user_id, session_id=session_id)

    def _generate_grounded_answer(self, message, retrieval, *, user_id=None, session_id=None):
        prompt = self._build_prompt(
            message,
            retrieval,
            conversation_history=self._recent_chat_history(
                user_id=user_id,
                session_id=session_id,
                current_message=message,
            ),
        )
        generated = self.openai_client.generate_answer(prompt=prompt, question=message)
        if generated:
            return generated
        return self._fallback_answer(message, retrieval)

    def _build_prompt(self, message, retrieval, *, conversation_history=None):
        source_lines = []
        for index, source in enumerate(retrieval["sources"], start=1):
            source_lines.append(
                f"[{index}] {source['title']} ({source['source_type']}): {source['excerpt']}"
            )
        graph_lines = []
        for row in retrieval["graph_context"]:
            graph_lines.append(f"- {row['type']}: {row['label']} (score={row['score']})")
        profile_lines = self._behavioral_profile_lines(retrieval.get("profile_snapshot") or {})
        history_lines = self._conversation_history_lines(conversation_history or [])

        return (
            "You are a warm and natural-sounding e-commerce assistant for a Vietnamese storefront. "
            "Answer in the same language as the user, and prefer natural Vietnamese with diacritics when the user writes Vietnamese. "
            "Use only the provided context for factual claims. "
            "Do not invent current price, stock, cart state, or order status unless it came from realtime API data. "
            "If the context is insufficient, say what is missing and ask one short follow-up question. "
            "Be helpful, clear, and conversational without sounding robotic.\n\n"
            f"Question: {message}\n\n"
            "Recent conversation:\n"
            + ("\n".join(history_lines) if history_lines else "No prior conversation.")
            + "\n\n"
            "Retrieved context:\n"
            + ("\n".join(source_lines) if source_lines else "No retrieved context.")
            + "\n\nGraph context:\n"
            + ("\n".join(graph_lines) if graph_lines else "No graph context.")
            + "\n\nBehavioral profile:\n"
            + ("\n".join(profile_lines) if profile_lines else "No behavioral profile.")
        )

    def _generate_general_answer(self, message, *, user_id=None, session_id=None):
        history_lines = self._conversation_history_lines(
            self._recent_chat_history(
                user_id=user_id,
                session_id=session_id,
                current_message=message,
            )
        )
        prompt = (
            "You are a warm, natural-sounding shopping assistant. "
            "Answer in the same language as the user, and prefer natural Vietnamese with diacritics when the user writes Vietnamese. "
            "If the request is broad, first give a helpful answer, then ask one short follow-up question. "
            "Do not invent realtime values such as exact stock, order status, or current price unless they were explicitly provided by APIs.\n\n"
            "Recent conversation:\n"
            + ("\n".join(history_lines) if history_lines else "No prior conversation.")
        )
        return self.openai_client.generate_answer(prompt=prompt, question=message)

    def _generate_greeting_answer(self, message, *, profile_snapshot, user_id=None, session_id=None):
        fallback = self._fallback_answer(message, {"sources": [], "graph_context": []})
        if not self.openai_client.enabled:
            return fallback

        prompt = (
            "You are a warm shopping assistant greeting a user for the first turn. "
            "Reply in the same language as the user, sounding natural and welcoming. "
            "Briefly explain the kinds of help you can provide in this store, and invite the user to describe their need. "
            "Do not invent realtime values or mention hidden system details.\n\n"
            "Behavioral profile:\n"
            + (
                "\n".join(self._behavioral_profile_lines(profile_snapshot))
                if profile_snapshot
                else "No behavioral profile."
            )
            + "\n\nFallback draft:\n"
            + fallback
        )
        generated = self.openai_client.generate_answer(prompt=prompt, question=message)
        return generated or fallback

    def _naturalize_realtime_answer(self, *, message, fallback_answer, facts, scope_label, user_id=None, session_id=None):
        if not self.openai_client.enabled:
            return fallback_answer

        history_lines = self._conversation_history_lines(
            self._recent_chat_history(
                user_id=user_id,
                session_id=session_id,
                current_message=message,
            )
        )
        prompt = (
            "You are a warm and natural-sounding shopping assistant. "
            "Rewrite the answer in the same language as the user. "
            "Use only the provided facts and do not add any new claims, numbers, or promises. "
            "Keep it concise, clear, and conversational. "
            "Avoid markdown code formatting and avoid sounding robotic.\n\n"
            f"Request type: {scope_label}\n"
            "Recent conversation:\n"
            + ("\n".join(history_lines) if history_lines else "No prior conversation.")
            + "\n\nFacts:\n"
            + json.dumps(facts, ensure_ascii=True)
            + "\n\nFallback draft:\n"
            + fallback_answer
        )
        generated = self.openai_client.generate_answer(prompt=prompt, question=message)
        return generated or fallback_answer

    def _general_fallback_answer(self):
        return (
            "Minh co the ho tro 2 nhom cau hoi: "
            "(1) du lieu he thong cua shop nhu san pham, gia, ton kho, gio hang, don hang, policy; "
            "(2) cau hoi tong quat khi ket noi AI ben ngoai kha dung. "
            "Ban hay noi ro muc tieu (vi du: 'goi y 3 ban phim yen tinh tam gia 1-2 trieu') de minh tu van dung hon."
        )

    def _should_use_general_answer(self, message, retrieval):
        normalized_message = self._normalize_text(message)
        if not normalized_message:
            return False

        if self._contains_any(normalized_message, CAPABILITY_QUESTION_KEYWORDS):
            return True

        if self._contains_any(normalized_message, ADVICE_KEYWORDS):
            return not self._has_product_context(retrieval)

        if self._contains_any(normalized_message, GREETING_KEYWORDS):
            return False

        if not self._contains_any(normalized_message, DOMAIN_INTENT_KEYWORDS):
            return True

        return False

    def _has_product_context(self, retrieval):
        for source in (retrieval.get("sources") or [])[:3]:
            if source.get("source_type") == "product":
                return True
        return False

    def _fallback_answer(self, message, retrieval):
        lowered_message = self._normalize_text(message)
        if not retrieval["sources"]:
            suggested_products = self._suggest_products(message=lowered_message, limit=3)
            if self._contains_any(lowered_message, GREETING_KEYWORDS):
                if suggested_products:
                    return (
                        "Chao ban! Minh co the tu van san pham, gia, ton kho, va trang thai don hang. "
                        f"Ban co the bat dau voi: {suggested_products}. "
                        "Thu hoi: 'gia cua Silent Keyboard Pro' hoac 'ton kho product_id 2'."
                    )
                return (
                    "Chao ban! Minh co the ho tro ve san pham, gia, ton kho, gio hang, va don hang. "
                    "Ban hay cho minh ten san pham hoac product_id de tra loi chinh xac hon."
                )

            if suggested_products:
                return (
                    "Minh chua co du ngu canh grounded cho cau hoi nay, nhung co the ho tro theo du lieu hien co. "
                    f"Mot so san pham ban co the tham khao: {suggested_products}. "
                    "Ban thu neu ro ten san pham hoac hoi dang 'gia/ton kho cua <ten san pham>'."
                )

            return (
                "Minh chua du ngu canh grounded de tra loi chac chan. "
                "Ban thu neu ro ten san pham, product_id, hoac cau hoi policy cu the hon nhe."
            )

        lead = retrieval["sources"][0]
        lead_excerpt = self._summarize_excerpt(lead.get("excerpt", ""))
        lead_excerpt = self._strip_leading_title_phrase(lead.get("title", ""), lead_excerpt)
        answer_parts = [lead_excerpt]
        if retrieval["graph_context"]:
            answer_parts.append(f"Recent graph context suggests interest around {retrieval['graph_context'][0]['label']}.")
        return " ".join(answer_parts)

    def _recent_chat_history(self, *, user_id=None, session_id=None, current_message=None):
        if user_id is None and not session_id:
            return []

        raw_events = self.interaction_client.fetch_events(
            user_id=user_id,
            session_id=session_id,
            limit=max(10, getattr(settings, "CHAT_HISTORY_LIMIT", 4) * 3),
        )
        current_normalized = self._normalize_text(current_message or "")
        history = []
        for row in raw_events:
            if row.get("event_type") != "chat_message_sent":
                continue
            query_text = (row.get("query_text") or "").strip()
            if not query_text:
                continue
            if current_normalized and self._normalize_text(query_text) == current_normalized:
                continue
            history.append(query_text)

        if not history:
            return []
        limit = getattr(settings, "CHAT_HISTORY_LIMIT", 4)
        return history[-limit:]

    def _conversation_history_lines(self, messages):
        return [f"- User: {message}" for message in messages if message]

    def _suggest_products(self, *, message, limit=3):
        try:
            products = self.product_client.fetch_products()
        except ServiceClientError:
            return ""

        query_tokens = self._tokens(message)
        candidates = []
        for product in products:
            if not product.get("is_active", False):
                continue
            if not product.get("has_stock", False):
                continue

            product_text = " ".join(
                [
                    str(product.get("name") or ""),
                    str(product.get("short_description") or ""),
                    " ".join(product.get("tags") or []),
                ]
            ).lower()
            product_tokens = self._tokens(product_text)
            overlap_score = len(query_tokens & product_tokens)
            candidates.append((overlap_score, product))

        if not candidates:
            return ""

        # If there is no lexical overlap, still suggest stable top in-stock products.
        candidates.sort(key=lambda item: (-item[0], int(item[1].get("id", 0))))
        top = [row[1] for row in candidates[:limit]]
        return ", ".join(
            f"{product.get('name')} (${product.get('base_price')})"
            for product in top
            if product.get("name")
        )

    def _resolve_product(self, products, *, explicit_product_id=None, message=""):
        if explicit_product_id is not None:
            for product in products:
                if int(product["id"]) == int(explicit_product_id):
                    return product
            return None

        lowered = self._normalize_text(message)
        best = None
        best_score = 0
        for product in products:
            name = self._normalize_text(product.get("name") or "")
            if not name:
                continue
            score = sum(1 for token in self._tokens(name) if token in lowered)
            if name in lowered:
                score += 5
            if score > best_score:
                best = product
                best_score = score
        return best if best_score > 0 else None

    def _chunk_to_source(self, chunk, score):
        excerpt = chunk.text.strip().replace("\n", " ")
        excerpt = excerpt[:220] + ("..." if len(excerpt) > 220 else "")
        return {
            "source_type": chunk.source_type,
            "source_id": chunk.source_id,
            "title": chunk.title,
            "excerpt": excerpt,
            "product_id": chunk.product_id,
            "score": round(float(score), 3),
        }

    def _profile_bias(self, chunk, profile_snapshot):
        if not profile_snapshot:
            return 0.0

        bias = 0.0
        top_category_ids = {
            row.get("category_id")
            for row in profile_snapshot.get("top_categories", [])
            if row.get("category_id") is not None
        }
        top_brand_ids = {
            row.get("brand_id")
            for row in profile_snapshot.get("top_brands", [])
            if row.get("brand_id") is not None
        }
        top_price_bands = {
            row.get("price_band")
            for row in profile_snapshot.get("top_price_bands", [])
            if row.get("price_band")
        }
        recent_product_ids = set(profile_snapshot.get("recent_viewed_product_ids", []))
        recent_product_ids.update(profile_snapshot.get("recent_clicked_product_ids", []))
        recent_product_ids.update(profile_snapshot.get("recent_carted_product_ids", []))
        recent_product_ids.update(profile_snapshot.get("recent_purchased_product_ids", []))
        strong_product_ids = {
            row.get("product_id")
            for row in profile_snapshot.get("strong_product_interests", [])
            if row.get("product_id") is not None
        }
        recent_query_tokens = self._tokens(" ".join(profile_snapshot.get("recent_queries", [])))
        recent_chat_tokens = self._tokens(" ".join(profile_snapshot.get("recent_chat_cues", [])))

        if chunk.product_id in recent_product_ids:
            bias += 2.0
        if chunk.product_id in strong_product_ids:
            bias += 1.4
        if chunk.category_id in top_category_ids:
            bias += 1.2
        if chunk.brand_id in top_brand_ids:
            bias += 0.8
        if top_price_bands and chunk.product_id is not None:
            product_price_band = self._extract_price_band(chunk.text)
            if product_price_band in top_price_bands:
                bias += 0.5
        if recent_query_tokens and recent_query_tokens & self._tokens(chunk.text):
            bias += 0.4
        if recent_chat_tokens and recent_chat_tokens & self._tokens(chunk.text):
            bias += 0.2
        return bias

    def _behavioral_profile_lines(self, profile_snapshot):
        if not profile_snapshot:
            return []

        top_category_ids = [str(row.get("category_id")) for row in profile_snapshot.get("top_categories", [])[:3]]
        top_brand_ids = [str(row.get("brand_id")) for row in profile_snapshot.get("top_brands", [])[:3]]
        recent_products = [str(product_id) for product_id in profile_snapshot.get("recent_product_ids", [])[:5]]
        recent_queries = profile_snapshot.get("recent_queries", [])[:3]

        lines = [
            f"- scope_type: {profile_snapshot.get('scope_type')}",
            f"- funnel_stage: {profile_snapshot.get('funnel_stage')}",
            f"- purchase_intent_score: {profile_snapshot.get('purchase_intent_score')}",
        ]
        if top_category_ids:
            lines.append(f"- top_categories: {', '.join(top_category_ids)}")
        if top_brand_ids:
            lines.append(f"- top_brands: {', '.join(top_brand_ids)}")
        if recent_products:
            lines.append(f"- recent_products: {', '.join(recent_products)}")
        if recent_queries:
            lines.append(f"- recent_queries: {' | '.join(recent_queries)}")
        return lines

    def _extract_price_band(self, text):
        lowered = text.lower()
        if "price=" not in lowered:
            return None
        match = re.search(r"price=([0-9]+(?:\.[0-9]+)?)", lowered)
        if not match:
            return None
        amount = float(match.group(1))
        if amount < 50:
            return "budget"
        if amount < 150:
            return "mid"
        if amount < 500:
            return "premium"
        return "luxury"

    def _product_text(self, product):
        fields = [
            product.get("name") or "",
            product.get("short_description") or "",
            product.get("full_description") or product.get("description") or "",
            f"category_id={product.get('category_id')}",
            f"brand_id={product.get('brand_id')}",
            f"price={product.get('base_price')}",
            "in stock" if product.get("has_stock") else "out of stock",
        ]
        attributes = product.get("attributes") or {}
        if attributes:
            fields.append("attributes: " + ", ".join(f"{key}={value}" for key, value in sorted(attributes.items())))
        tags = product.get("tags") or []
        if tags:
            fields.append("tags: " + ", ".join(tags))
        return ". ".join(str(field) for field in fields if field not in {"", "None"})

    def _split_text(self, text, max_chars=500):
        normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if not normalized:
            return []
        if len(normalized) <= max_chars:
            return [normalized]
        chunks = []
        start = 0
        while start < len(normalized):
            end = min(start + max_chars, len(normalized))
            chunks.append(normalized[start:end])
            start = end
        return chunks

    def _summarize_excerpt(self, excerpt, max_chars=280):
        cleaned = self._clean_markdown_text(excerpt)
        if not cleaned:
            return "I found relevant context, but it needs a more specific follow-up question."

        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        summary_parts = []
        current_length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            extra_length = len(sentence) + (1 if summary_parts else 0)
            if current_length + extra_length > max_chars:
                break
            summary_parts.append(sentence)
            current_length += extra_length
            if len(summary_parts) >= 2:
                break

        if summary_parts:
            return " ".join(summary_parts)

        truncated = cleaned[:max_chars].rstrip()
        if len(cleaned) > max_chars:
            truncated += "..."
        return truncated

    def _clean_markdown_text(self, text):
        if not text:
            return ""

        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = re.sub(r"^#{1,6}\s*", "", line)
            line = re.sub(r"^[-*+]\s+", "", line)
            line = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", line)
            line = line.replace("`", "")
            lines.append(line)

        normalized = " ".join(lines)
        return re.sub(r"\s+", " ", normalized).strip()

    def _strip_leading_title_phrase(self, title, excerpt):
        if not title or not excerpt:
            return excerpt

        title_clean = re.sub(r"[^a-z0-9 ]+", " ", title.lower())
        title_tokens = [token for token in title_clean.split() if token]
        if not title_tokens:
            return excerpt

        excerpt_words = excerpt.split()
        lower_words = [re.sub(r"[^a-z0-9]+", "", word.lower()) for word in excerpt_words]

        # Remove leading repeated title phrase (e.g., "Shipping Policy" when title is "Shipping").
        if lower_words and lower_words[0] in title_tokens:
            cut_index = 0
            while cut_index < len(lower_words):
                token = lower_words[cut_index]
                if not token:
                    cut_index += 1
                    continue
                if token in title_tokens or token == "policy":
                    cut_index += 1
                    continue
                break
            stripped = " ".join(excerpt_words[cut_index:]).strip()
            if stripped:
                return stripped

        return excerpt

    def _tokens(self, text):
        normalized = self._normalize_text(text)
        return {token for token in TOKEN_PATTERN.findall(normalized) if len(token) >= 2}

    def _contains_any(self, text, keywords):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return False
        padded = f" {normalized_text} "
        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            if normalized_keyword and f" {normalized_keyword} " in padded:
                return True
        return False

    def _is_greeting_message(self, text):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return False

        greeting_match = any(
            normalized_text == keyword or normalized_text.startswith(f"{keyword} ")
            for keyword in GREETING_KEYWORDS
        )
        if not greeting_match:
            return False

        intent_keywords = (
            "price",
            "gia",
            "stock",
            "ton kho",
            "order",
            "don hang",
            "shipping",
            "payment",
            "return",
            "policy",
            "cart",
            "gio hang",
            "faq",
        )
        if self._contains_any(normalized_text, intent_keywords):
            return False

        return len(normalized_text.split()) <= 6

    def _is_order_status_question(self, text, *, order_id=None):
        if order_id is not None:
            return True
        normalized = self._normalize_text(text)
        order_terms_present = self._contains_any(normalized, ("order", "don hang"))
        if not order_terms_present:
            return False
        return self._contains_any(normalized, ORDER_STATUS_TERMS)

    def _normalize_text(self, text):
        if not text:
            return ""
        lowered = str(text).lower()
        decomposed = unicodedata.normalize("NFKD", lowered)
        no_diacritics = "".join(char for char in decomposed if not unicodedata.combining(char))
        ascii_only = no_diacritics.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only).strip()

    def _cosine_similarity(self, left, right):
        if not left or not right:
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
