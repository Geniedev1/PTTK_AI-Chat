from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

LABEL_EVENT_SCORES = {
    "order_paid": 1.0,
    "order_completed": 1.0,
    "cart_item_added": 0.7,
    "product_clicked": 0.4,
    "product_viewed": 0.2,
}

PRODUCT_SIGNAL_WEIGHTS = {
    "product_viewed": 1.0,
    "product_clicked": 1.5,
    "cart_item_added": 3.0,
    "cart_item_quantity_updated": 2.0,
    "checkout_started": 3.5,
    "order_created": 4.0,
    "order_paid": 5.0,
    "order_completed": 5.0,
}

SAMPLE_TRIGGER_EVENTS = {
    "product_viewed",
    "product_clicked",
    "cart_item_added",
    "cart_item_quantity_updated",
    "checkout_started",
    "order_created",
    "order_paid",
    "order_completed",
}


def parse_timestamp(value):
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def actor_key_from_event(event):
    user_id = event.get("user_id")
    if user_id is not None:
        try:
            return "user:%s" % int(user_id)
        except (TypeError, ValueError):
            return None
    session_id = str(event.get("session_id") or "").strip()
    if session_id:
        return "session:%s" % session_id
    return None


def normalize_events(raw_events):
    normalized = []
    for raw in raw_events:
        actor_key = actor_key_from_event(raw)
        if not actor_key:
            continue
        timestamp = parse_timestamp(raw.get("timestamp"))
        if timestamp is None:
            continue

        product_id = raw.get("product_id")
        try:
            product_id = int(product_id) if product_id is not None else None
        except (TypeError, ValueError):
            product_id = None

        normalized.append(
            {
                "actor_key": actor_key,
                "scope_type": "user" if actor_key.startswith("user:") else "session",
                "event_type": raw.get("event_type") or "",
                "product_id": product_id,
                "timestamp": timestamp,
                "signal_weight": float(raw.get("signal_weight", 0) or 0),
            }
        )
    normalized.sort(key=lambda row: (row["timestamp"], row["actor_key"], row.get("product_id") or 0))
    return normalized


def normalize_products(raw_products):
    products = {}
    for row in raw_products:
        product_id = row.get("id")
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            continue
        products[product_id] = row
    return products


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _price_band(value):
    amount = _to_decimal(value)
    if amount is None:
        return None
    if amount < Decimal("50"):
        return "budget"
    if amount < Decimal("150"):
        return "mid"
    if amount < Decimal("500"):
        return "premium"
    return "luxury"


def _count_events(rows, *, now, days, event_types=None, product_id=None):
    lower = now - timedelta(days=days)
    count = 0
    for row in rows:
        if row["timestamp"] < lower or row["timestamp"] >= now:
            continue
        if event_types is not None and row["event_type"] not in event_types:
            continue
        if product_id is not None and row.get("product_id") != product_id:
            continue
        count += 1
    return count


def _history_preferences(actor_history, products, *, now):
    weighted_categories = Counter()
    weighted_brands = Counter()

    for row in actor_history:
        if row["timestamp"] >= now:
            continue
        product_id = row.get("product_id")
        if product_id not in products:
            continue
        product = products[product_id]
        weight = PRODUCT_SIGNAL_WEIGHTS.get(row["event_type"], 0.0)
        if weight <= 0:
            continue
        category_id = product.get("category_id")
        brand_id = product.get("brand_id")
        if category_id is not None:
            weighted_categories[int(category_id)] += weight
        if brand_id is not None:
            weighted_brands[int(brand_id)] += weight

    top_category = weighted_categories.most_common(1)
    top_brand = weighted_brands.most_common(1)
    return {
        "actor_top_category_id": top_category[0][0] if top_category else None,
        "actor_top_brand_id": top_brand[0][0] if top_brand else None,
    }


def _purchase_intent_pre(actor_history, *, now):
    view_count = _count_events(actor_history, now=now, days=30, event_types={"product_viewed"})
    click_count = _count_events(actor_history, now=now, days=30, event_types={"product_clicked"})
    cart_count = _count_events(
        actor_history,
        now=now,
        days=30,
        event_types={"cart_item_added", "cart_item_quantity_updated"},
    )
    checkout_count = _count_events(
        actor_history,
        now=now,
        days=30,
        event_types={"checkout_started", "order_created"},
    )
    purchase_count = _count_events(
        actor_history,
        now=now,
        days=30,
        event_types={"order_paid", "order_completed"},
    )
    score = min(
        (
            view_count * 0.04
            + click_count * 0.07
            + cart_count * 0.18
            + checkout_count * 0.26
            + purchase_count * 0.35
        ),
        1.0,
    )
    return round(float(score), 4)


def _item_popularity_pre(item_history, *, now):
    score = 0.0
    for row in item_history:
        if row["timestamp"] >= now:
            continue
        score += {
            "product_viewed": 0.4,
            "product_clicked": 0.8,
            "cart_item_added": 1.5,
            "order_paid": 2.5,
            "order_completed": 2.5,
        }.get(row["event_type"], 0.0)
    return round(score, 4)


def _label_from_window(pair_rows, *, snapshot_time, label_window_days):
    window_end = snapshot_time + timedelta(days=label_window_days)
    best_score = 0.0
    best_type = None
    best_timestamp = None
    strong_conversion = False

    for row in pair_rows:
        ts = row["timestamp"]
        if ts < snapshot_time or ts > window_end:
            continue
        event_type = row["event_type"]
        score = LABEL_EVENT_SCORES.get(event_type)
        if score is None:
            continue
        if score >= 0.7:
            strong_conversion = True
        if score > best_score:
            best_score = score
            best_type = event_type
            best_timestamp = ts

    weak_negative = int((not strong_conversion) and best_score in {0.2, 0.4})
    return {
        "binary_label": int(strong_conversion),
        "weighted_label": round(float(best_score), 4),
        "weak_negative": weak_negative,
        "label_event_type": best_type,
        "label_timestamp": best_timestamp.isoformat() if best_timestamp else None,
        "label_window_end": window_end.isoformat(),
    }


def build_dataset_records(raw_events, raw_products, *, label_window_days=14):
    events = normalize_events(raw_events)
    products = normalize_products(raw_products)

    actor_history = defaultdict(list)
    actor_item_history = defaultdict(list)
    item_history = defaultdict(list)

    pair_event_index = defaultdict(list)
    for row in events:
        product_id = row.get("product_id")
        if product_id is None:
            continue
        pair_event_index[(row["actor_key"], product_id)].append(row)

    samples = []
    seen_pairs = set()

    for row in events:
        actor_key = row["actor_key"]
        now = row["timestamp"]
        product_id = row.get("product_id")

        if (
            product_id in products
            and row["event_type"] in SAMPLE_TRIGGER_EVENTS
            and (actor_key, product_id) not in seen_pairs
        ):
            seen_pairs.add((actor_key, product_id))
            product = products[product_id]
            actor_rows = actor_history[actor_key]
            actor_item_rows = actor_item_history[(actor_key, product_id)]
            item_rows = item_history[product_id]
            pref = _history_preferences(actor_rows, products, now=now)

            sample = {
                "sample_id": "%s|%s|%s" % (actor_key, product_id, now.isoformat()),
                "actor_key": actor_key,
                "scope_type": row["scope_type"],
                "product_id": product_id,
                "snapshot_time": now.isoformat(),
                "feature_cutoff_time": now.isoformat(),
                "item_category_id": product.get("category_id"),
                "item_brand_id": product.get("brand_id"),
                "item_product_type_id": product.get("product_type_id"),
                "item_price_band": _price_band(product.get("base_price")),
                "item_has_stock": int(bool(product.get("has_stock", False))),
                "item_is_active": int(bool(product.get("is_active", False))),
                "actor_top_category_id": pref["actor_top_category_id"],
                "actor_top_brand_id": pref["actor_top_brand_id"],
                "actor_purchase_intent_pre": _purchase_intent_pre(actor_rows, now=now),
                "actor_event_count_1d": _count_events(actor_rows, now=now, days=1),
                "actor_event_count_7d": _count_events(actor_rows, now=now, days=7),
                "actor_event_count_30d": _count_events(actor_rows, now=now, days=30),
                "actor_view_count_7d": _count_events(actor_rows, now=now, days=7, event_types={"product_viewed"}),
                "actor_click_count_7d": _count_events(actor_rows, now=now, days=7, event_types={"product_clicked"}),
                "actor_cart_count_7d": _count_events(
                    actor_rows,
                    now=now,
                    days=7,
                    event_types={"cart_item_added", "cart_item_quantity_updated"},
                ),
                "actor_purchase_count_30d": _count_events(
                    actor_rows,
                    now=now,
                    days=30,
                    event_types={"order_paid", "order_completed"},
                ),
                "actor_item_event_count_30d": _count_events(actor_item_rows, now=now, days=30),
                "item_popularity_pre": _item_popularity_pre(item_rows, now=now),
                "interaction_overlap_pre": _count_events(
                    actor_item_rows,
                    now=now,
                    days=30,
                    event_types={"product_viewed", "product_clicked", "cart_item_added", "order_paid", "order_completed"},
                ),
                "graph_neighbor_score_pre": 0.0,
            }
            samples.append(sample)

        actor_history[actor_key].append(row)
        if product_id is not None:
            actor_item_history[(actor_key, product_id)].append(row)
            item_history[product_id].append(row)

    for sample in samples:
        snapshot_time = parse_timestamp(sample["snapshot_time"])
        label = _label_from_window(
            pair_event_index[(sample["actor_key"], sample["product_id"])],
            snapshot_time=snapshot_time,
            label_window_days=label_window_days,
        )
        sample.update(label)

    samples.sort(key=lambda row: row["snapshot_time"])
    return samples


def split_samples_by_actor_time(samples, *, train_ratio=0.7, valid_ratio=0.15):
    actor_first_seen = {}
    for row in samples:
        actor = row["actor_key"]
        ts = parse_timestamp(row["snapshot_time"])
        if actor not in actor_first_seen or ts < actor_first_seen[actor]:
            actor_first_seen[actor] = ts

    ordered_actors = sorted(actor_first_seen.items(), key=lambda item: (item[1], item[0]))
    actor_count = len(ordered_actors)
    if actor_count == 0:
        return {"train": [], "valid": [], "test": []}, {
            "split_method": "time_based_actor_bucket",
            "actor_count": 0,
            "train_ratio": train_ratio,
            "valid_ratio": valid_ratio,
            "test_ratio": max(0.0, 1.0 - train_ratio - valid_ratio),
            "time_boundaries": {},
        }

    train_count = max(1, int(actor_count * train_ratio))
    valid_count = max(1, int(actor_count * valid_ratio)) if actor_count >= 3 else 0
    if train_count + valid_count >= actor_count:
        valid_count = max(0, actor_count - train_count - 1)
    test_count = actor_count - train_count - valid_count
    if test_count <= 0:
        test_count = 1
        if valid_count > 0:
            valid_count -= 1
        else:
            train_count = max(1, train_count - 1)

    train_actors = {actor for actor, _ in ordered_actors[:train_count]}
    valid_actors = {actor for actor, _ in ordered_actors[train_count : train_count + valid_count]}

    splits = {"train": [], "valid": [], "test": []}
    for row in samples:
        actor = row["actor_key"]
        if actor in train_actors:
            split = "train"
        elif actor in valid_actors:
            split = "valid"
        else:
            split = "test"
        row["split"] = split
        splits[split].append(row)

    boundaries = {}
    if splits["train"]:
        boundaries["train_end"] = max(row["snapshot_time"] for row in splits["train"])
    if splits["valid"]:
        boundaries["valid_end"] = max(row["snapshot_time"] for row in splits["valid"])

    metadata = {
        "split_method": "time_based_actor_bucket",
        "actor_count": actor_count,
        "train_ratio": train_ratio,
        "valid_ratio": valid_ratio,
        "test_ratio": max(0.0, 1.0 - train_ratio - valid_ratio),
        "actor_split_counts": {
            "train": len(train_actors),
            "valid": len(valid_actors),
            "test": actor_count - len(train_actors) - len(valid_actors),
        },
        "time_boundaries": boundaries,
    }
    return splits, metadata


def build_quality_report(samples, splits):
    total = len(samples)
    key_fields = [
        "actor_key",
        "product_id",
        "snapshot_time",
        "item_category_id",
        "item_brand_id",
        "item_price_band",
    ]

    null_counts = {}
    for field in key_fields:
        null_counts[field] = sum(1 for row in samples if row.get(field) in (None, ""))

    duplicates = set()
    seen = set()
    for row in samples:
        key = (row.get("actor_key"), row.get("product_id"), row.get("snapshot_time"))
        if key in seen:
            duplicates.add(key)
        seen.add(key)

    leakage_count = 0
    for row in samples:
        label_ts = parse_timestamp(row.get("label_timestamp"))
        snapshot_ts = parse_timestamp(row.get("snapshot_time"))
        if label_ts is not None and snapshot_ts is not None and label_ts < snapshot_ts:
            leakage_count += 1

    positive_count = sum(1 for row in samples if int(row.get("binary_label", 0)) == 1)
    weak_negative_count = sum(1 for row in samples if int(row.get("weak_negative", 0)) == 1)

    split_counts = {name: len(rows) for name, rows in splits.items()}
    min_split_size = min(split_counts.values()) if split_counts else 0

    return {
        "record_count": total,
        "actor_count": len({row.get("actor_key") for row in samples}),
        "product_count": len({row.get("product_id") for row in samples}),
        "class_balance": {
            "binary_positive_count": positive_count,
            "binary_positive_rate": round((positive_count / total), 4) if total else 0.0,
            "weak_negative_count": weak_negative_count,
            "weak_negative_rate": round((weak_negative_count / total), 4) if total else 0.0,
        },
        "null_ratio": {
            field: round((count / total), 4) if total else 0.0
            for field, count in null_counts.items()
        },
        "duplicate_row_count": len(duplicates),
        "leakage_check": {
            "label_before_snapshot_count": leakage_count,
            "passed": leakage_count == 0,
        },
        "split_counts": split_counts,
        "minimum_split_size": min_split_size,
    }
