# Knowledge Graph Evidence (Plan 05)

## 1. Graph Schema & Mapping

**Nodes**:
- `User` (Actor)
- `Session` (Actor)
- `Product`
- `Category`
- `Brand`
- `Query`

**Edges & Behavior Mapping**:
The behaviors from the `data_user500.csv` dataset were correctly mapped into Neo4j relationship types:
- `product_viewed` -> `VIEWED`
- `product_clicked` -> `CLICKED`
- `cart_item_added` -> `ADDED_TO_CART`
- `cart_item_removed` -> `REMOVED_FROM_CART`
- `cart_item_quantity_updated` -> `UPDATED_CART`
- `order_paid` / `order_completed` -> `PURCHASED`
- `order_cancelled` -> `CANCELLED_ORDER`
- `search_performed` -> `SEARCHED`

Weighted Edges added:
Each interaction edge inherently stores `count`, `weight`, `last_interacted_at`, and an array of `event_types`. 

## 2. Graph Status Output

The graph was rebuilt successfully using `python manage.py rebuild_graph` in the `interaction-service`. Neo4j successfully processed actions from the synthesized dataset. 

*Node & Edge Metrics generated via `/graph/status`:*
```json
{
  "enabled": true,
  "node_counts": {
    "Category": 8,
    "Product": 30,
    "Query": 17,
    "Session": 559,
    "User": 368
  },
  "relationship_counts": {
    "ADDED_TO_CART": 845,
    "BELONGS_TO": 30,
    "CANCELLED_ORDER": 135,
    "CLICKED": 1033,
    "IDENTIFIED_AS": 559,
    "INTERACTED_WITH": 1034,
    "PURCHASED": 721,
    "REMOVED_FROM_CART": 218,
    "SEARCHED": 2701,
    "UPDATED_CART": 521,
    "VIEWED": 1033
  }
}
```

## 3. Query Demo Outputs

### Top Categories by User Interest (User 10)
Returns the top categories a user is implicitly interested in, aggregated across products they interacted with.
```json
[
  {
    "category_id": 2,
    "category_name": "Category 2",
    "total_weight": 26,
    "distinct_products": 1
  },
  {
    "category_id": 8,
    "category_name": "Category 8",
    "total_weight": 24,
    "distinct_products": 1
  },
  {
    "category_id": 1,
    "category_name": "Category 1",
    "total_weight": 3,
    "distinct_products": 1
  }
]
```

### Similar Users (User 10)
Locates other Users who interacted with the exact same sets of items, factoring in interaction weights.
```json
[
  {
    "actor_id": 492,
    "similarity_score": 53,
    "shared_products": 3
  },
  {
    "actor_id": 368,
    "similarity_score": 29,
    "shared_products": 2
  },
  {
    "actor_id": 101,
    "similarity_score": 27,
    "shared_products": 2
  }
]
```
