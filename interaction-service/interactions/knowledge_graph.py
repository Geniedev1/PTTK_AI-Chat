import json
import logging
from functools import lru_cache

import requests
from django.conf import settings
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


logger = logging.getLogger(__name__)

PRODUCT_EDGE_TYPES = {
    "product_viewed": "VIEWED",
    "product_clicked": "CLICKED",
    "cart_item_added": "ADDED_TO_CART",
    "cart_item_removed": "REMOVED_FROM_CART",
    "cart_item_quantity_updated": "UPDATED_CART",
    "order_paid": "PURCHASED",
    "order_completed": "PURCHASED",
    "order_cancelled": "CANCELLED_ORDER",
}


class ProductCatalogClient:
    def __init__(self):
        self.base_url = getattr(settings, "PRODUCT_SERVICE_URL", "").rstrip("/")
        admin_key = getattr(settings, "INTERNAL_ADMIN_KEY", "")
        self.headers = {"X-Internal-Admin-Key": admin_key} if admin_key else {}

    def _fetch(self, path, params=None):
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params or {},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def fetch_categories(self):
        if not self.base_url:
            return []
        return self._fetch("/api/products/categories/")

    def fetch_products(self):
        if not self.base_url:
            return []
        return self._fetch("/api/products/", params={"include_inactive": "true"})


class KnowledgeGraphStore:
    def __init__(self, uri, user, password):
        self.uri = (uri or "").strip()
        self.user = user
        self.password = password
        self.driver = None
        if self.enabled:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    @property
    def enabled(self):
        return bool(self.uri and self.user and self.password)

    def _run(self, query, **params):
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    def _safe_execute(self, callback, default):
        if not self.enabled:
            return default
        try:
            return callback()
        except (Neo4jError, OSError, ValueError, requests.RequestException, Exception) as exc:
            logger.warning("Knowledge graph operation failed: %s", exc)
            return default

    def status(self):
        if not self.enabled:
            return {
                "enabled": False,
                "graph_sync_on_write": getattr(settings, "GRAPH_SYNC_ON_WRITE", True),
            }

        def _query_status():
            node_rows = self._run(
                """
                MATCH (n)
                WITH CASE
                    WHEN 'Product' IN labels(n) THEN 'Product'
                    WHEN 'Category' IN labels(n) THEN 'Category'
                    WHEN 'Brand' IN labels(n) THEN 'Brand'
                    WHEN 'Query' IN labels(n) THEN 'Query'
                    WHEN 'User' IN labels(n) THEN 'User'
                    WHEN 'Session' IN labels(n) THEN 'Session'
                    ELSE 'Other'
                END AS label, count(*) AS total
                RETURN label, total
                ORDER BY label
                """
            )
            relation_rows = self._run(
                """
                MATCH ()-[r]->()
                RETURN type(r) AS relation_type, count(*) AS total
                ORDER BY relation_type
                """
            )
            return {
                "enabled": True,
                "connected": True,
                "graph_sync_on_write": getattr(settings, "GRAPH_SYNC_ON_WRITE", True),
                "node_counts": {row["label"]: row["total"] for row in node_rows},
                "relationship_counts": {row["relation_type"]: row["total"] for row in relation_rows},
            }

        return self._safe_execute(_query_status, {"enabled": True, "connected": False})

    def clear_graph(self):
        return self._safe_execute(lambda: self._run("MATCH (n) DETACH DELETE n"), [])

    def sync_product_catalog(self, products, categories):
        if not self.enabled:
            return {"synced_products": 0, "synced_categories": 0}

        def _sync():
            category_count = 0
            product_count = 0
            for category in categories:
                self._run(
                    """
                    MERGE (c:Category {category_id: $category_id})
                    SET c.name = $name,
                        c.slug = $slug,
                        c.parent_id = $parent_id
                    """,
                    category_id=category["id"],
                    name=category.get("name"),
                    slug=category.get("slug"),
                    parent_id=category.get("parent"),
                )
                category_count += 1

            for product in products:
                self._run(
                    """
                    MERGE (p:Product {product_id: $product_id})
                    SET p.name = $name,
                        p.slug = $slug,
                        p.short_description = $short_description,
                        p.description = $description,
                        p.base_price = $base_price,
                        p.stock = $stock,
                        p.is_active = $is_active,
                        p.status = $status,
                        p.tags = $tags,
                        p.attributes_json = $attributes_json,
                        p.product_type_id = $product_type_id
                    """,
                    product_id=product["id"],
                    name=product.get("name"),
                    slug=product.get("slug"),
                    short_description=product.get("short_description"),
                    description=product.get("full_description") or product.get("description"),
                    base_price=str(product.get("base_price")),
                    stock=product.get("stock", 0),
                    is_active=product.get("is_active", False),
                    status=product.get("status"),
                    tags=product.get("tags", []),
                    attributes_json=json.dumps(product.get("attributes", {}), sort_keys=True),
                    product_type_id=product.get("product_type_id"),
                )

                category_id = product.get("category_id")
                if category_id:
                    self._run(
                        """
                        MERGE (c:Category {category_id: $category_id})
                        MERGE (p:Product {product_id: $product_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        category_id=category_id,
                        product_id=product["id"],
                    )

                brand_id = product.get("brand_id")
                if brand_id:
                    self._run(
                        """
                        MERGE (b:Brand {brand_id: $brand_id})
                        ON CREATE SET b.name = $brand_name
                        MERGE (p:Product {product_id: $product_id})
                        MERGE (p)-[:OF_BRAND]->(b)
                        """,
                        brand_id=brand_id,
                        brand_name=f"Brand {brand_id}",
                        product_id=product["id"],
                    )
                product_count += 1

            return {
                "synced_products": product_count,
                "synced_categories": category_count,
            }

        return self._safe_execute(_sync, {"synced_products": 0, "synced_categories": 0})

    def _merge_actor(self, user_id=None, session_id=None):
        actor = None
        if user_id is not None:
            actor = {"label": "User", "field": "user_id", "value": int(user_id)}
            self._run(
                "MERGE (:Actor:User {user_id: $user_id})",
                user_id=int(user_id),
            )
        if session_id:
            session_id = str(session_id)
            self._run(
                "MERGE (:Actor:Session {session_id: $session_id})",
                session_id=session_id,
            )
            if user_id is not None:
                self._run(
                    """
                    MERGE (s:Actor:Session {session_id: $session_id})
                    MERGE (u:Actor:User {user_id: $user_id})
                    MERGE (s)-[:IDENTIFIED_AS]->(u)
                    """,
                    session_id=session_id,
                    user_id=int(user_id),
                )
            if actor is None:
                actor = {"label": "Session", "field": "session_id", "value": session_id}
        return actor

    def _merge_weighted_relationship(self, source_label, source_field, source_value, relation_type, target_label, target_field, target_value, event):
        self._run(
            f"""
            MATCH (source:Actor:{source_label} {{{source_field}: $source_value}})
            MERGE (target:{target_label} {{{target_field}: $target_value}})
            MERGE (source)-[rel:{relation_type}]->(target)
            SET rel.count = coalesce(rel.count, 0) + 1,
                rel.weight = coalesce(rel.weight, 0) + $signal_weight,
                rel.last_interacted_at = $timestamp,
                rel.last_event_type = $event_type,
                rel.event_types = CASE
                    WHEN rel.event_types IS NULL THEN [$event_type]
                    WHEN $event_type IN rel.event_types THEN rel.event_types
                    ELSE rel.event_types + $event_type
                END
            """,
            source_value=source_value,
            target_value=target_value,
            signal_weight=event["signal_weight"],
            timestamp=event["timestamp"],
            event_type=event["event_type"],
        )

    def sync_interaction_event(self, event):
        if not self.enabled:
            return False

        def _sync():
            actor = self._merge_actor(event.get("user_id"), event.get("session_id"))
            if actor is None:
                return False

            query_text = (event.get("query_text") or "").strip()
            if query_text:
                self._run(
                    """
                    MERGE (q:Query {text: $query_text})
                    SET q.last_seen_at = $timestamp
                    """,
                    query_text=query_text,
                    timestamp=event["timestamp"],
                )
                self._merge_weighted_relationship(
                    actor["label"],
                    actor["field"],
                    actor["value"],
                    "SEARCHED",
                    "Query",
                    "text",
                    query_text,
                    event,
                )

                for product_id in event.get("metadata", {}).get("product_ids", [])[:10]:
                    self._run(
                        """
                        MERGE (q:Query {text: $query_text})
                        MERGE (p:Product {product_id: $product_id})
                        MERGE (q)-[rel:MATCHES]->(p)
                        SET rel.count = coalesce(rel.count, 0) + 1,
                            rel.weight = coalesce(rel.weight, 0) + $signal_weight,
                            rel.last_seen_at = $timestamp
                        """,
                        query_text=query_text,
                        product_id=int(product_id),
                        signal_weight=event["signal_weight"],
                        timestamp=event["timestamp"],
                    )

            product_id = event.get("product_id")
            if product_id is not None:
                self._run(
                    """
                    MERGE (p:Product {product_id: $product_id})
                    SET p.last_seen_at = $timestamp
                    """,
                    product_id=int(product_id),
                    timestamp=event["timestamp"],
                )
                self._merge_weighted_relationship(
                    actor["label"],
                    actor["field"],
                    actor["value"],
                    "INTERACTED_WITH",
                    "Product",
                    "product_id",
                    int(product_id),
                    event,
                )

                relation_type = PRODUCT_EDGE_TYPES.get(event["event_type"])
                if relation_type:
                    self._merge_weighted_relationship(
                        actor["label"],
                        actor["field"],
                        actor["value"],
                        relation_type,
                        "Product",
                        "product_id",
                        int(product_id),
                        event,
                    )

                category_id = event.get("metadata", {}).get("category_id")
                if category_id:
                    self._run(
                        """
                        MERGE (c:Category {category_id: $category_id})
                        MERGE (p:Product {product_id: $product_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        category_id=int(category_id),
                        product_id=int(product_id),
                    )

                brand_id = event.get("metadata", {}).get("brand_id")
                if brand_id:
                    self._run(
                        """
                        MERGE (b:Brand {brand_id: $brand_id})
                        ON CREATE SET b.name = $brand_name
                        MERGE (p:Product {product_id: $product_id})
                        MERGE (p)-[:OF_BRAND]->(b)
                        """,
                        brand_id=int(brand_id),
                        brand_name=f"Brand {brand_id}",
                        product_id=int(product_id),
                    )
            return True

        return self._safe_execute(_sync, False)

    def refresh_similarity_edges(self):
        if not self.enabled:
            return {"updated_pairs": 0}

        def _refresh():
            self._run("MATCH (:Product)-[r:SIMILAR_TO]->(:Product) DELETE r")
            rows = self._run(
                """
                MATCH (p1:Product)<-[r1:INTERACTED_WITH]-(a:Actor)-[r2:INTERACTED_WITH]->(p2:Product)
                WHERE p1.product_id < p2.product_id
                WITH p1, p2, SUM(CASE WHEN r1.weight < r2.weight THEN r1.weight ELSE r2.weight END) AS overlap_weight,
                     COUNT(DISTINCT a) AS shared_actor_count
                OPTIONAL MATCH (p1)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(p2)
                WITH p1, p2, overlap_weight, shared_actor_count, CASE WHEN c IS NULL THEN 0 ELSE 2 END AS category_bonus
                OPTIONAL MATCH (p1)-[:OF_BRAND]->(b:Brand)<-[:OF_BRAND]-(p2)
                WITH p1, p2, overlap_weight, shared_actor_count, category_bonus, CASE WHEN b IS NULL THEN 0 ELSE 1 END AS brand_bonus
                WITH p1, p2, overlap_weight + category_bonus + brand_bonus AS similarity_score,
                     shared_actor_count, category_bonus, brand_bonus
                WHERE similarity_score > 0
                MERGE (p1)-[r1:SIMILAR_TO]->(p2)
                SET r1.score = similarity_score,
                    r1.shared_actor_count = shared_actor_count,
                    r1.category_bonus = category_bonus,
                    r1.brand_bonus = brand_bonus
                MERGE (p2)-[r2:SIMILAR_TO]->(p1)
                SET r2.score = similarity_score,
                    r2.shared_actor_count = shared_actor_count,
                    r2.category_bonus = category_bonus,
                    r2.brand_bonus = brand_bonus
                RETURN count(*) AS updated_pairs
                """
            )
            return {"updated_pairs": rows[0]["updated_pairs"] if rows else 0}

        return self._safe_execute(_refresh, {"updated_pairs": 0})

    def rebuild_graph(self, products, categories, interactions):
        if not self.enabled:
            return {
                "enabled": False,
                "synced_products": 0,
                "synced_categories": 0,
                "synced_interactions": 0,
                "updated_pairs": 0,
            }

        self.clear_graph()
        catalog_result = self.sync_product_catalog(products, categories)
        synced_interactions = 0
        for event in interactions:
            if self.sync_interaction_event(event):
                synced_interactions += 1
        similarity_result = self.refresh_similarity_edges()
        return {
            "enabled": True,
            "synced_products": catalog_result["synced_products"],
            "synced_categories": catalog_result["synced_categories"],
            "synced_interactions": synced_interactions,
            "updated_pairs": similarity_result["updated_pairs"],
        }

    def user_interest(self, *, user_id=None, session_id=None, limit=10):
        if not self.enabled:
            return []
        label = "User" if user_id is not None else "Session"
        field = "user_id" if user_id is not None else "session_id"
        value = int(user_id) if user_id is not None else str(session_id)

        def _query():
            return self._run(
                f"""
                MATCH (actor:Actor:{label} {{{field}: $value}})-[r:INTERACTED_WITH]->(p:Product)-[:BELONGS_TO]->(c:Category)
                RETURN c.category_id AS category_id,
                       COALESCE(c.name, 'Category ' + toString(c.category_id)) AS category_name,
                       SUM(r.weight) AS total_weight,
                       COUNT(DISTINCT p) AS distinct_products
                ORDER BY total_weight DESC, distinct_products DESC, category_id
                LIMIT $limit
                """,
                value=value,
                limit=limit,
            )

        return self._safe_execute(_query, [])

    def product_neighbors(self, product_id, limit=10):
        if not self.enabled:
            return []

        def _query():
            rows = self._run(
                """
                MATCH (p:Product {product_id: $product_id})-[r:SIMILAR_TO]->(other:Product)
                RETURN other.product_id AS product_id,
                       COALESCE(other.name, 'Product ' + toString(other.product_id)) AS product_name,
                       r.score AS similarity_score,
                       r.shared_actor_count AS shared_actor_count,
                       r.category_bonus AS category_bonus,
                       r.brand_bonus AS brand_bonus
                ORDER BY similarity_score DESC, shared_actor_count DESC, product_id
                LIMIT $limit
                """,
                product_id=int(product_id),
                limit=limit,
            )
            if rows:
                return rows
            return self._run(
                """
                MATCH (p:Product {product_id: $product_id})<-[r1:INTERACTED_WITH]-(a:Actor)-[r2:INTERACTED_WITH]->(other:Product)
                WHERE other.product_id <> $product_id
                WITH other, SUM(CASE WHEN r1.weight < r2.weight THEN r1.weight ELSE r2.weight END) AS similarity_score,
                     COUNT(DISTINCT a) AS shared_actor_count
                RETURN other.product_id AS product_id,
                       COALESCE(other.name, 'Product ' + toString(other.product_id)) AS product_name,
                       similarity_score,
                       shared_actor_count,
                       0 AS category_bonus,
                       0 AS brand_bonus
                ORDER BY similarity_score DESC, shared_actor_count DESC, product_id
                LIMIT $limit
                """,
                product_id=int(product_id),
                limit=limit,
            )

        return self._safe_execute(_query, [])

    def query_paths(self, *, product_id=None, query_text=None, limit=10):
        if not self.enabled:
            return []

        def _query():
            if product_id is not None:
                return self._run(
                    """
                    MATCH (q:Query)-[r:MATCHES]->(p:Product {product_id: $product_id})
                    RETURN q.text AS query_text,
                           r.count AS match_count,
                           r.weight AS total_weight
                    ORDER BY total_weight DESC, match_count DESC, query_text
                    LIMIT $limit
                    """,
                    product_id=int(product_id),
                    limit=limit,
                )
            return self._run(
                """
                MATCH (q:Query {text: $query_text})-[r:MATCHES]->(p:Product)
                OPTIONAL MATCH (p)<-[iw:INTERACTED_WITH]-(:Actor)
                RETURN p.product_id AS product_id,
                       COALESCE(p.name, 'Product ' + toString(p.product_id)) AS product_name,
                       r.count AS match_count,
                       r.weight AS total_weight,
                       COALESCE(SUM(iw.weight), 0) AS product_interest_weight
                ORDER BY total_weight DESC, product_interest_weight DESC, product_id
                LIMIT $limit
                """,
                query_text=str(query_text),
                limit=limit,
            )

        return self._safe_execute(_query, [])

    def similar_users(self, *, user_id=None, session_id=None, limit=10):
        if not self.enabled:
            return []
        label = "User" if user_id is not None else "Session"
        field = "user_id" if user_id is not None else "session_id"
        value = int(user_id) if user_id is not None else str(session_id)
        other_field = "user_id" if user_id is not None else "session_id"

        def _query():
            return self._run(
                f"""
                MATCH (actor:Actor:{label} {{{field}: $value}})-[r1:INTERACTED_WITH]->(p:Product)<-[r2:INTERACTED_WITH]-(other:Actor:{label})
                WHERE other.{other_field} <> $value
                RETURN other.{other_field} AS actor_id,
                       SUM(CASE WHEN r1.weight < r2.weight THEN r1.weight ELSE r2.weight END) AS similarity_score,
                       COUNT(DISTINCT p) AS shared_products
                ORDER BY similarity_score DESC, shared_products DESC, actor_id
                LIMIT $limit
                """,
                value=value,
                limit=limit,
            )

        return self._safe_execute(_query, [])


@lru_cache(maxsize=1)
def get_graph_store():
    return KnowledgeGraphStore(
        getattr(settings, "NEO4J_URI", ""),
        getattr(settings, "NEO4J_USER", "neo4j"),
        getattr(settings, "NEO4J_PASSWORD", ""),
    )
