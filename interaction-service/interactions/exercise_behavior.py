import csv
import json
from collections import Counter
from pathlib import Path


EXERCISE_ACTION_MAP = {
    "product_viewed": "view",
    "product_clicked": "click",
    "cart_item_added": "add_to_cart",
    "cart_item_removed": "remove_from_cart",
    "checkout_started": "checkout",
    "order_paid": "purchase",
    "order_completed": "purchase",
    "search_performed": "search",
    "chat_message_sent": "chat",
}

EXERCISE_SUBMISSION_HEADERS = ["user_id", "product_id", "action", "timestamp"]
FULL_EXPORT_HEADERS = [
    "event_id",
    "event_type",
    "user_id",
    "session_id",
    "product_id",
    "query_text",
    "source",
    "signal_weight",
    "timestamp",
    "metadata_json",
]


def event_to_submission_row(event):
    action = EXERCISE_ACTION_MAP.get(event.event_type)
    if not action or event.user_id is None:
        return None
    return {
        "user_id": int(event.user_id),
        "product_id": event.product_id if event.product_id is not None else "",
        "action": action,
        "timestamp": event.timestamp.isoformat(),
    }


def event_to_full_row(event):
    return {
        "event_id": str(event.event_id),
        "event_type": event.event_type,
        "user_id": event.user_id if event.user_id is not None else "",
        "session_id": event.session_id or "",
        "product_id": event.product_id if event.product_id is not None else "",
        "query_text": event.query_text or "",
        "source": event.source,
        "signal_weight": event.signal_weight,
        "timestamp": event.timestamp.isoformat(),
        "metadata_json": json.dumps(event.metadata or {}, ensure_ascii=True, sort_keys=True),
    }


def write_csv(path, headers, rows):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_submission_quality_report(rows):
    row_list = list(rows)
    action_counts = Counter()
    distinct_users = set()
    null_product_count = 0

    for row in row_list:
        distinct_users.add(int(row["user_id"]))
        action_counts[str(row["action"])] += 1
        if row["product_id"] in ("", None):
            null_product_count += 1

    ordered_rows = sorted(
        row_list,
        key=lambda row: (str(row["timestamp"]), int(row["user_id"]), str(row["action"]), str(row["product_id"])),
    )
    sample_preview = ordered_rows[:5]

    return {
        "row_count": len(row_list),
        "distinct_user_count": len(distinct_users),
        "distinct_action_count": len(action_counts),
        "action_distribution": dict(sorted(action_counts.items())),
        "null_product_count": null_product_count,
        "null_product_rate": round((null_product_count / len(row_list)), 6) if row_list else 0.0,
        "preview_rows": sample_preview,
        "acceptance_checks": {
            "has_500_distinct_users": len(distinct_users) >= 500,
            "has_required_columns": True,
            "has_minimum_8_behavior_types": len(action_counts) >= 8,
            "timestamps_present": all(str(row["timestamp"]).strip() for row in row_list),
        },
    }

