# RAG Chat with Knowledge Graph Evidence (Plan 06)

## 1. Graph Context Integration Strategy

The RAG pipeline retrieves and constructs system prompts using 3 primary sources of context:
1. **Local Graph Retrieval**: Queries Neo4j (via `used_graph_context=true`) for the User's implicit interests (Categories), and Product similarity networks (Neighbors).
2. **Deep Behavioral Intents**: Calculates funnel status and extracts textual search keywords from the `InteractionEvent` history.
3. **Real-time API Routing**: Recognizes explicit questions about live product state (like current stock or pricing) and fetches directly from the downstream services (ex: Cart, Order) skipping the static graph cache.

## 2. Chat Transcripts

> Test scenario hitting `/api/ai/chat`. The logs show `used_graph_context` triggering where applicable to shape the AI's answer.

### Transcript A: User Implicit Preference Recommendations

**Prompt**: "Gợi ý cho tôi vài sản phẩm theo thể loại sở thích của tôi đi" (Suggest some products based on my favorite categories)
**Context Flags**: `used_graph_context=true`, `retrieval_mode=user-profile`
**Sources Extracted via Graph**:
- Implicit Interest matches from Neo4j (Category 2, Category 8, Category 1)
- Historic strong product interactions 

**Extracted JSON Payload snippet**:
```json
{
  "answer": "Based on your behavior and what you've viewed, you seem highly interested in Category 8 and Category 2 products. Specifically, I highly recommend checking out similar products like 'Plan 5 Smoke Keyboard'.",
  "used_realtime_api": false,
  "used_graph_context": true,
  "retrieval_mode": "user-profile",
  "profile_snapshot": {
    "preference_summary": {
      "graph_interest_summary": [
        { "category_id": 2, "category_name": "Category 2", "score": 26.0 },
        { "category_id": 8, "category_name": "Category 8", "score": 24.0 },
        { "category_id": 1, "category_name": "Category 1", "score": 3.0 }
      ]
    }
  }
}
```

### Transcript B: Graph Product Node Neighbors (Similarity)

**Prompt**: "Sản phẩm này có gì tương tự không?" (Is there anything similar to this product?)
**Context Flags**: `used_graph_context=true`, `retrieval_mode=product-neighbors`

**Extracted JSON Payload snippet**:
```json
{
  "answer": "Yes! Because many people who liked this product also interacted with other items in Category 8, I can recommend the 'Plan 8 Granite Table'. Both items share a high co-interaction metric.",
  "used_realtime_api": false,
  "used_graph_context": true,
  "retrieval_mode": "product-neighbors",
  "sources": [
    {
      "source_id": "product_neighbor_12",
      "type": "product_neighbor",
      "content": "Similar product via graph: Plan 8 Granite Table (ID 12) - similarity_score: 1.5, shared_actors: 2"
    }
  ]
}
```

### Transcript C: Real-Time Fallback (Intent override)

**Prompt**: "Sản phẩm này còn hàng không? Giá bao nhiêu?" (Is this product in stock? How much is it?)
**Context Flags**: `used_realtime_api=true`, `used_graph_context=false`, `retrieval_mode=realtime-product`

*As required by the exercise, realtime questions bypassed the static graph to fetch the most up-to-date representation via REST APIs.*
