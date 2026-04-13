from collections import Counter


def build_profile_snapshot(products, events, interest_rows):
    recent_viewed_product_ids = []
    recent_queries = []
    seen_viewed = set()
    seen_queries = set()
    category_counter = Counter()
    brand_counter = Counter()

    for event in events:
        signal_weight = max(float(event.get("signal_weight", 1) or 1), 1.0)
        product_id = event.get("product_id")
        event_type = event.get("event_type")
        query_text = (event.get("query_text") or "").strip()

        if query_text and query_text not in seen_queries:
            recent_queries.append(query_text)
            seen_queries.add(query_text)

        if product_id in products:
            product = products[product_id]
            category_id = product.get("category_id")
            brand_id = product.get("brand_id")
            if category_id is not None:
                category_counter[int(category_id)] += signal_weight
            if brand_id is not None:
                brand_counter[int(brand_id)] += signal_weight
            if event_type == "product_viewed" and product_id not in seen_viewed:
                recent_viewed_product_ids.append(int(product_id))
                seen_viewed.add(int(product_id))

    top_categories = [
        {"category_id": category_id, "score": round(float(score), 2)}
        for category_id, score in category_counter.most_common(3)
    ]
    top_brands = [
        {"brand_id": brand_id, "score": round(float(score), 2)}
        for brand_id, score in brand_counter.most_common(3)
    ]
    graph_interest_summary = [
        {
            "category_id": row.get("category_id"),
            "category_name": row.get("category_name"),
            "score": round(float(row.get("total_weight", 0)), 2),
        }
        for row in interest_rows[:3]
    ]

    return {
        "top_categories": top_categories,
        "top_brands": top_brands,
        "recent_viewed_product_ids": recent_viewed_product_ids[:5],
        "recent_queries": recent_queries[:5],
        "graph_interest_summary": graph_interest_summary,
    }
