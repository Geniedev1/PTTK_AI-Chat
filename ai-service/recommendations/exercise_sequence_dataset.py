from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ACTION_VOCAB = {
    "PAD": 0,
    "view": 1,
    "click": 2,
    "add_to_cart": 3,
    "remove_from_cart": 4,
    "checkout": 5,
    "purchase": 6,
    "search": 7,
    "chat": 8,
}

ACTION_MAP = {
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

POSITIVE_ACTIONS = {"add_to_cart", "checkout", "purchase"}


@dataclass
class SequenceSample:
    actor_key: str
    actor_id: int
    snapshot_time: str
    label: int
    sequence_length: int
    action_ids: list[int]
    product_ids: list[int]
    category_ids: list[int]
    time_delta_hours: list[float]
    session_positions: list[float]
    mask: list[int]


def _parse_timestamp(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_full_behavior_csv(path):
    rows = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            event_type = str(raw.get("event_type") or "").strip()
            action = ACTION_MAP.get(event_type)
            user_id = raw.get("user_id")
            if not action or user_id in (None, ""):
                continue

            try:
                timestamp = _parse_timestamp(raw.get("timestamp"))
            except ValueError:
                continue
            if timestamp is None:
                continue

            try:
                actor_id = int(user_id)
            except (TypeError, ValueError):
                continue

            metadata = {}
            metadata_json = str(raw.get("metadata_json") or "").strip()
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                except json.JSONDecodeError:
                    metadata = {}

            product_id = raw.get("product_id")
            try:
                product_id = int(product_id) if product_id not in (None, "") else 0
            except (TypeError, ValueError):
                product_id = 0

            category_id = metadata.get("category_id", 0)
            try:
                category_id = int(category_id) if category_id not in (None, "") else 0
            except (TypeError, ValueError):
                category_id = 0

            rows.append(
                {
                    "actor_key": "user:%s" % actor_id,
                    "actor_id": actor_id,
                    "session_id": str(raw.get("session_id") or "").strip(),
                    "event_type": event_type,
                    "action": action,
                    "action_id": ACTION_VOCAB[action],
                    "product_id": product_id,
                    "category_id": category_id,
                    "timestamp": timestamp,
                }
            )

    rows.sort(key=lambda row: (row["timestamp"], row["actor_id"], row["session_id"], row["action_id"]))
    return rows


def build_sequence_samples(rows, *, max_sequence_length=12, prediction_horizon=3, min_history=2):
    actor_events = {}
    for row in rows:
        actor_events.setdefault(row["actor_key"], []).append(row)

    samples = []
    for actor_key, events in actor_events.items():
        session_positions = Counter()
        for event in events:
            session_key = event["session_id"] or actor_key
            session_positions[session_key] += 1
            event["session_position"] = session_positions[session_key]

        for index in range(min_history, len(events)):
            history = events[max(0, index - max_sequence_length):index]
            if len(history) < min_history:
                continue
            future = events[index:index + prediction_horizon]
            label = 1 if any(row["action"] in POSITIVE_ACTIONS for row in future) else 0

            anchor_time = history[-1]["timestamp"]
            action_ids = []
            product_ids = []
            category_ids = []
            time_delta_hours = []
            session_positions_list = []
            mask = []

            for row in history[-max_sequence_length:]:
                delta_hours = max(0.0, (anchor_time - row["timestamp"]).total_seconds() / 3600.0)
                action_ids.append(int(row["action_id"]))
                product_ids.append(int(row["product_id"]))
                category_ids.append(int(row["category_id"]))
                time_delta_hours.append(float(min(delta_hours, 24.0 * 14.0)))
                session_positions_list.append(float(min(int(row["session_position"]), 50)))
                mask.append(1)

            actual_length = len(action_ids)
            while len(action_ids) < max_sequence_length:
                action_ids.insert(0, 0)
                product_ids.insert(0, 0)
                category_ids.insert(0, 0)
                time_delta_hours.insert(0, 0.0)
                session_positions_list.insert(0, 0.0)
                mask.insert(0, 0)

            samples.append(
                SequenceSample(
                    actor_key=actor_key,
                    actor_id=int(events[0]["actor_id"]),
                    snapshot_time=anchor_time.isoformat(),
                    label=label,
                    sequence_length=actual_length,
                    action_ids=action_ids,
                    product_ids=product_ids,
                    category_ids=category_ids,
                    time_delta_hours=time_delta_hours,
                    session_positions=session_positions_list,
                    mask=mask,
                )
            )

    samples.sort(key=lambda row: (row.snapshot_time, row.actor_key))
    return samples


def split_samples_by_actor(samples, *, train_ratio=0.7, valid_ratio=0.15):
    actor_order = {}
    for sample in samples:
        ts = _parse_timestamp(sample.snapshot_time)
        if sample.actor_key not in actor_order or ts < actor_order[sample.actor_key]:
            actor_order[sample.actor_key] = ts

    ordered = sorted(actor_order.items(), key=lambda item: (item[1], item[0]))
    actor_count = len(ordered)
    if actor_count == 0:
        return {"train": [], "valid": [], "test": []}, {"actor_count": 0}

    train_count = max(1, int(actor_count * train_ratio))
    valid_count = max(1, int(actor_count * valid_ratio)) if actor_count >= 3 else 0
    if train_count + valid_count >= actor_count:
        valid_count = max(0, actor_count - train_count - 1)

    train_actors = {actor for actor, _ in ordered[:train_count]}
    valid_actors = {actor for actor, _ in ordered[train_count:train_count + valid_count]}

    splits = {"train": [], "valid": [], "test": []}
    for sample in samples:
        if sample.actor_key in train_actors:
            splits["train"].append(sample)
        elif sample.actor_key in valid_actors:
            splits["valid"].append(sample)
        else:
            splits["test"].append(sample)

    metadata = {
        "actor_count": actor_count,
        "actor_split_counts": {
            "train": len(train_actors),
            "valid": len(valid_actors),
            "test": actor_count - len(train_actors) - len(valid_actors),
        },
        "sample_split_counts": {name: len(rows) for name, rows in splits.items()},
        "split_method": "actor_time_bucket",
    }
    return splits, metadata


def _normalize_per_timestep(values):
    arr = np.asarray(values, dtype=np.float64)
    max_value = float(arr.max()) if arr.size else 1.0
    if max_value <= 0:
        max_value = 1.0
    return arr / max_value, max_value


def encode_split(samples):
    if not samples:
        return {
            "action_ids": np.zeros((0, 0), dtype=np.int64),
            "product_ids": np.zeros((0, 0), dtype=np.int64),
            "category_ids": np.zeros((0, 0), dtype=np.int64),
            "time_delta_hours": np.zeros((0, 0), dtype=np.float64),
            "session_positions": np.zeros((0, 0), dtype=np.float64),
            "mask": np.zeros((0, 0), dtype=np.float64),
            "labels": np.zeros((0,), dtype=np.float64),
            "actor_ids": np.zeros((0,), dtype=np.int64),
        }

    return {
        "action_ids": np.asarray([sample.action_ids for sample in samples], dtype=np.int64),
        "product_ids": np.asarray([sample.product_ids for sample in samples], dtype=np.int64),
        "category_ids": np.asarray([sample.category_ids for sample in samples], dtype=np.int64),
        "time_delta_hours": np.asarray([sample.time_delta_hours for sample in samples], dtype=np.float64),
        "session_positions": np.asarray([sample.session_positions for sample in samples], dtype=np.float64),
        "mask": np.asarray([sample.mask for sample in samples], dtype=np.float64),
        "labels": np.asarray([sample.label for sample in samples], dtype=np.float64),
        "actor_ids": np.asarray([sample.actor_id for sample in samples], dtype=np.int64),
    }


def build_sequence_artifacts(
    csv_path,
    *,
    max_sequence_length=12,
    prediction_horizon=3,
    min_history=2,
    train_ratio=0.7,
    valid_ratio=0.15,
):
    rows = load_full_behavior_csv(csv_path)
    samples = build_sequence_samples(
        rows,
        max_sequence_length=max_sequence_length,
        prediction_horizon=prediction_horizon,
        min_history=min_history,
    )
    splits, split_meta = split_samples_by_actor(samples, train_ratio=train_ratio, valid_ratio=valid_ratio)

    encoded = {name: encode_split(split_rows) for name, split_rows in splits.items()}

    all_product_ids = [product_id for sample in samples for product_id, mask in zip(sample.product_ids, sample.mask) if mask]
    all_category_ids = [category_id for sample in samples for category_id, mask in zip(sample.category_ids, sample.mask) if mask]
    _, product_scale = _normalize_per_timestep(all_product_ids)
    _, category_scale = _normalize_per_timestep(all_category_ids)

    stats = {
        "sample_count": len(samples),
        "actor_count": len({sample.actor_key for sample in samples}),
        "positive_count": int(sum(sample.label for sample in samples)),
        "positive_rate": round((sum(sample.label for sample in samples) / len(samples)), 6) if samples else 0.0,
        "sequence_length_summary": {
            "min": min((sample.sequence_length for sample in samples), default=0),
            "max": max((sample.sequence_length for sample in samples), default=0),
            "avg": round((sum(sample.sequence_length for sample in samples) / len(samples)), 4) if samples else 0.0,
        },
        "split": split_meta,
    }
    preprocess_config = {
        "max_sequence_length": max_sequence_length,
        "prediction_horizon": prediction_horizon,
        "min_history": min_history,
        "action_vocab": ACTION_VOCAB,
        "product_id_scale": product_scale,
        "category_id_scale": category_scale,
        "time_delta_hours_clip": 24.0 * 14.0,
        "session_position_clip": 50.0,
    }
    return {
        "rows": rows,
        "samples": samples,
        "splits": splits,
        "encoded": encoded,
        "stats": stats,
        "preprocess_config": preprocess_config,
    }


def save_sequence_artifacts(output_dir, artifact_bundle):
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    for split_name, payload in artifact_bundle["encoded"].items():
        np.savez(output_path / f"{split_name}.npz", **payload)

    protocol = {
        "task": "binary_purchase_intent_from_behavior_sequence",
        "positive_actions": sorted(POSITIVE_ACTIONS),
        "sequence_unit": "actor_history_window",
        "feature_version": "exercise-sequence-v1",
        "stats": artifact_bundle["stats"],
    }

    (output_path / "protocol.json").write_text(
        json.dumps(protocol, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_path / "vocab.json").write_text(
        json.dumps({"action_vocab": ACTION_VOCAB}, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_path / "label_map.json").write_text(
        json.dumps({"0": "low_intent", "1": "high_intent"}, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_path / "preprocess_config.json").write_text(
        json.dumps(artifact_bundle["preprocess_config"], ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    preview = []
    for sample in artifact_bundle["samples"][:3]:
        preview.append(
            {
                "actor_key": sample.actor_key,
                "snapshot_time": sample.snapshot_time,
                "label": sample.label,
                "sequence_length": sample.sequence_length,
                "action_ids": sample.action_ids,
                "product_ids": sample.product_ids,
                "category_ids": sample.category_ids,
            }
        )
    (output_path / "sample_preview.json").write_text(
        json.dumps(preview, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return {
        "output_dir": str(output_path),
        "stats": artifact_bundle["stats"],
    }
