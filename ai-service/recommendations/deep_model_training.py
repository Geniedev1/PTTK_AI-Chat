from __future__ import annotations

import json
import math
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import numpy as np

NUMERIC_FEATURE_FIELDS = (
    "actor_purchase_intent_pre",
    "actor_event_count_1d",
    "actor_event_count_7d",
    "actor_event_count_30d",
    "actor_view_count_7d",
    "actor_click_count_7d",
    "actor_cart_count_7d",
    "actor_purchase_count_30d",
    "actor_item_event_count_30d",
    "item_popularity_pre",
    "interaction_overlap_pre",
    "graph_neighbor_score_pre",
    "item_has_stock",
    "item_is_active",
)

CATEGORICAL_FEATURE_FIELDS = (
    "scope_type",
    "item_category_id",
    "item_brand_id",
    "item_product_type_id",
    "item_price_band",
    "actor_top_category_id",
    "actor_top_brand_id",
)


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_jsonl(path):
    rows = []
    file_path = Path(path)
    if not file_path.exists():
        return rows
    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


class FeaturePreprocessor:
    def __init__(self, numeric_fields=None, categorical_fields=None):
        self.numeric_fields = list(numeric_fields or NUMERIC_FEATURE_FIELDS)
        self.categorical_fields = list(categorical_fields or CATEGORICAL_FEATURE_FIELDS)
        self.numeric_means = {}
        self.numeric_stds = {}
        self.categorical_vocab = {}
        self.categorical_offsets = {}
        self.input_dim = 0

    def fit(self, rows):
        numeric_values = {field: [] for field in self.numeric_fields}
        for row in rows:
            for field in self.numeric_fields:
                numeric_values[field].append(_safe_float(row.get(field)))

        for field in self.numeric_fields:
            values = np.asarray(numeric_values[field], dtype=np.float64)
            mean = float(values.mean()) if len(values) else 0.0
            std = float(values.std()) if len(values) else 0.0
            if std < 1e-6:
                std = 1.0
            self.numeric_means[field] = mean
            self.numeric_stds[field] = std

        offset = len(self.numeric_fields)
        for field in self.categorical_fields:
            seen_values = []
            seen_set = set()
            for row in rows:
                raw_value = row.get(field)
                if raw_value in (None, ""):
                    continue
                token = str(raw_value)
                if token in seen_set:
                    continue
                seen_set.add(token)
                seen_values.append(token)
            seen_values.sort()
            self.categorical_vocab[field] = {token: idx for idx, token in enumerate(seen_values)}
            self.categorical_offsets[field] = offset
            offset += len(seen_values)

        self.input_dim = offset
        return self

    def transform(self, rows):
        matrix = np.zeros((len(rows), self.input_dim), dtype=np.float64)
        if len(rows) == 0:
            return matrix

        for row_idx, row in enumerate(rows):
            for col_idx, field in enumerate(self.numeric_fields):
                value = _safe_float(row.get(field))
                matrix[row_idx, col_idx] = (value - self.numeric_means[field]) / self.numeric_stds[field]

            for field in self.categorical_fields:
                raw_value = row.get(field)
                if raw_value in (None, ""):
                    continue
                token = str(raw_value)
                vocab = self.categorical_vocab.get(field) or {}
                if token not in vocab:
                    continue
                col_idx = self.categorical_offsets[field] + vocab[token]
                matrix[row_idx, col_idx] = 1.0
        return matrix

    def labels(self, rows):
        return np.asarray([_safe_float(row.get("binary_label")) for row in rows], dtype=np.float64)

    def to_dict(self):
        return {
            "numeric_fields": list(self.numeric_fields),
            "categorical_fields": list(self.categorical_fields),
            "numeric_means": {k: float(v) for k, v in self.numeric_means.items()},
            "numeric_stds": {k: float(v) for k, v in self.numeric_stds.items()},
            "categorical_vocab": {
                field: {token: int(index) for token, index in vocab.items()}
                for field, vocab in self.categorical_vocab.items()
            },
            "categorical_offsets": {field: int(offset) for field, offset in self.categorical_offsets.items()},
            "input_dim": int(self.input_dim),
        }


class NumpyMLPBinaryClassifier:
    def __init__(self, input_dim, hidden_dims=(32, 16), seed=42):
        if input_dim <= 0:
            raise ValueError("input_dim must be > 0")
        if not hidden_dims:
            raise ValueError("hidden_dims must not be empty")

        self.input_dim = int(input_dim)
        self.hidden_dims = tuple(int(dim) for dim in hidden_dims)
        self.seed = int(seed)

        layer_dims = [self.input_dim] + list(self.hidden_dims) + [1]
        rng = np.random.default_rng(self.seed)
        self.weights = []
        self.biases = []
        for layer_idx in range(len(layer_dims) - 1):
            fan_in = layer_dims[layer_idx]
            fan_out = layer_dims[layer_idx + 1]
            weight = rng.normal(0.0, math.sqrt(2.0 / max(1, fan_in)), size=(fan_in, fan_out))
            bias = np.zeros((1, fan_out), dtype=np.float64)
            self.weights.append(weight.astype(np.float64))
            self.biases.append(bias)

    def copy_state(self):
        return {
            "weights": [np.array(weight, copy=True) for weight in self.weights],
            "biases": [np.array(bias, copy=True) for bias in self.biases],
        }

    def load_state(self, state):
        self.weights = [np.array(weight, copy=True) for weight in state["weights"]]
        self.biases = [np.array(bias, copy=True) for bias in state["biases"]]

    def _forward_with_cache(self, x_batch, *, training=False, dropout_rate=0.0, rng=None):
        activations = [x_batch]
        pre_activations = []
        dropout_masks = []

        current = x_batch
        for layer_idx in range(len(self.weights) - 1):
            z_val = current @ self.weights[layer_idx] + self.biases[layer_idx]
            pre_activations.append(z_val)
            current = np.maximum(z_val, 0.0)
            if training and dropout_rate > 0.0:
                keep_prob = 1.0 - dropout_rate
                mask = (rng.random(current.shape) < keep_prob).astype(np.float64) / keep_prob
                current = current * mask
            else:
                mask = None
            dropout_masks.append(mask)
            activations.append(current)

        z_out = current @ self.weights[-1] + self.biases[-1]
        pre_activations.append(z_out)
        y_hat = 1.0 / (1.0 + np.exp(-np.clip(z_out, -35.0, 35.0)))
        activations.append(y_hat)
        return y_hat, activations, pre_activations, dropout_masks

    def predict_proba(self, x_matrix):
        if len(x_matrix) == 0:
            return np.asarray([], dtype=np.float64)
        y_hat, _, _, _ = self._forward_with_cache(x_matrix, training=False)
        return y_hat.reshape(-1)

    def train(
        self,
        x_train,
        y_train,
        x_valid,
        y_valid,
        *,
        learning_rate=0.01,
        batch_size=16,
        epochs=120,
        dropout_rate=0.1,
        patience=15,
        seed=42,
    ):
        if len(x_train) == 0:
            raise ValueError("x_train must not be empty")

        batch_size = max(1, int(batch_size))
        epochs = max(1, int(epochs))
        patience = max(1, int(patience))

        m_weights = [np.zeros_like(weight) for weight in self.weights]
        v_weights = [np.zeros_like(weight) for weight in self.weights]
        m_biases = [np.zeros_like(bias) for bias in self.biases]
        v_biases = [np.zeros_like(bias) for bias in self.biases]

        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8
        step = 0

        rng = np.random.default_rng(seed)
        best_state = self.copy_state()
        best_epoch = 0
        best_valid_auc = -1.0
        no_improve = 0
        history = []

        y_train_col = y_train.reshape(-1, 1)

        for epoch_idx in range(1, epochs + 1):
            permutation = rng.permutation(len(x_train))
            x_epoch = x_train[permutation]
            y_epoch = y_train_col[permutation]

            for start in range(0, len(x_epoch), batch_size):
                end = min(start + batch_size, len(x_epoch))
                x_batch = x_epoch[start:end]
                y_batch = y_epoch[start:end]

                y_hat, activations, pre_activations, dropout_masks = self._forward_with_cache(
                    x_batch,
                    training=True,
                    dropout_rate=dropout_rate,
                    rng=rng,
                )

                sample_count = max(1, len(x_batch))
                gradients_w = [None] * len(self.weights)
                gradients_b = [None] * len(self.biases)

                dz = (y_hat - y_batch) / sample_count
                gradients_w[-1] = activations[-2].T @ dz
                gradients_b[-1] = np.sum(dz, axis=0, keepdims=True)
                da = dz @ self.weights[-1].T

                for hidden_idx in range(len(self.weights) - 2, -1, -1):
                    if dropout_masks[hidden_idx] is not None:
                        da = da * dropout_masks[hidden_idx]
                    dz = da * (pre_activations[hidden_idx] > 0.0)
                    gradients_w[hidden_idx] = activations[hidden_idx].T @ dz
                    gradients_b[hidden_idx] = np.sum(dz, axis=0, keepdims=True)
                    if hidden_idx > 0:
                        da = dz @ self.weights[hidden_idx].T

                for layer_idx in range(len(self.weights)):
                    step += 1
                    m_weights[layer_idx] = beta1 * m_weights[layer_idx] + (1.0 - beta1) * gradients_w[layer_idx]
                    v_weights[layer_idx] = beta2 * v_weights[layer_idx] + (1.0 - beta2) * (gradients_w[layer_idx] ** 2)
                    m_biases[layer_idx] = beta1 * m_biases[layer_idx] + (1.0 - beta1) * gradients_b[layer_idx]
                    v_biases[layer_idx] = beta2 * v_biases[layer_idx] + (1.0 - beta2) * (gradients_b[layer_idx] ** 2)

                    mhat_w = m_weights[layer_idx] / (1.0 - (beta1 ** step))
                    vhat_w = v_weights[layer_idx] / (1.0 - (beta2 ** step))
                    mhat_b = m_biases[layer_idx] / (1.0 - (beta1 ** step))
                    vhat_b = v_biases[layer_idx] / (1.0 - (beta2 ** step))

                    self.weights[layer_idx] -= learning_rate * mhat_w / (np.sqrt(vhat_w) + epsilon)
                    self.biases[layer_idx] -= learning_rate * mhat_b / (np.sqrt(vhat_b) + epsilon)

            train_scores = self.predict_proba(x_train)
            valid_scores = self.predict_proba(x_valid) if len(x_valid) else np.asarray([], dtype=np.float64)

            train_loss = binary_cross_entropy(y_train, train_scores)
            valid_loss = binary_cross_entropy(y_valid, valid_scores) if len(y_valid) else 0.0
            valid_auc = auc_score(y_valid, valid_scores) if len(y_valid) else 0.5

            history.append(
                {
                    "epoch": epoch_idx,
                    "train_loss": round(float(train_loss), 6),
                    "valid_loss": round(float(valid_loss), 6),
                    "valid_auc": round(float(valid_auc), 6),
                }
            )

            if valid_auc > best_valid_auc + 1e-7:
                best_valid_auc = valid_auc
                best_epoch = epoch_idx
                best_state = self.copy_state()
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= patience:
                    break

        self.load_state(best_state)
        return {
            "best_epoch": best_epoch,
            "best_valid_auc": float(best_valid_auc),
            "history": history,
        }


def binary_cross_entropy(y_true, y_score):
    if len(y_true) == 0:
        return 0.0
    eps = 1e-9
    clipped = np.clip(y_score, eps, 1.0 - eps)
    loss = -np.mean(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))
    return float(loss)


def auc_score(y_true, y_score):
    y_true = np.asarray(y_true, dtype=np.float64)
    y_score = np.asarray(y_score, dtype=np.float64)
    if len(y_true) == 0:
        return 0.5

    positives = y_true >= 0.5
    n_pos = int(positives.sum())
    n_neg = int(len(y_true) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return 0.5

    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(len(y_score), dtype=np.float64)
    ranks[order] = np.arange(1, len(y_score) + 1, dtype=np.float64)

    pos_rank_sum = float(ranks[positives].sum())
    auc = (pos_rank_sum - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return float(auc)


def precision_recall_f1(y_true, y_score, threshold=0.5):
    if len(y_true) == 0:
        return 0.0, 0.0, 0.0

    y_true_bin = (np.asarray(y_true) >= 0.5).astype(np.int64)
    y_pred_bin = (np.asarray(y_score) >= threshold).astype(np.int64)

    tp = int(((y_true_bin == 1) & (y_pred_bin == 1)).sum())
    fp = int(((y_true_bin == 0) & (y_pred_bin == 1)).sum())
    fn = int(((y_true_bin == 1) & (y_pred_bin == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = (2.0 * precision * recall) / (precision + recall)
    return float(precision), float(recall), float(f1)


def recall_at_k(y_true, y_score, k):
    if len(y_true) == 0:
        return 0.0
    positives = int((np.asarray(y_true) >= 0.5).sum())
    if positives == 0:
        return 0.0

    k_eff = max(1, min(int(k), len(y_true)))
    indices = np.argsort(np.asarray(y_score))[::-1][:k_eff]
    top_hits = int((np.asarray(y_true)[indices] >= 0.5).sum())
    return float(top_hits / positives)


def ndcg_at_k(y_true, y_score, k):
    if len(y_true) == 0:
        return 0.0

    k_eff = max(1, min(int(k), len(y_true)))
    y_true_arr = np.asarray(y_true, dtype=np.float64)
    y_score_arr = np.asarray(y_score, dtype=np.float64)

    ranked_idx = np.argsort(y_score_arr)[::-1][:k_eff]
    gains = y_true_arr[ranked_idx]
    dcg = 0.0
    for idx, gain in enumerate(gains):
        dcg += ((2.0 ** gain) - 1.0) / math.log2(idx + 2.0)

    ideal_gains = np.sort(y_true_arr)[::-1][:k_eff]
    idcg = 0.0
    for idx, gain in enumerate(ideal_gains):
        idcg += ((2.0 ** gain) - 1.0) / math.log2(idx + 2.0)

    if idcg <= 0.0:
        return 0.0
    return float(dcg / idcg)


def evaluate_split(rows, y_true, y_score):
    precision, recall, f1 = precision_recall_f1(y_true, y_score)
    metrics = {
        "sample_count": int(len(rows)),
        "positive_count": int((np.asarray(y_true) >= 0.5).sum()) if len(y_true) else 0,
        "positive_rate": round(float((np.asarray(y_true) >= 0.5).mean()), 6) if len(y_true) else 0.0,
        "auc": round(float(auc_score(y_true, y_score)), 6),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "recall_at_5": round(float(recall_at_k(y_true, y_score, 5)), 6),
        "recall_at_10": round(float(recall_at_k(y_true, y_score, 10)), 6),
        "ndcg_at_5": round(float(ndcg_at_k(y_true, y_score, 5)), 6),
        "ndcg_at_10": round(float(ndcg_at_k(y_true, y_score, 10)), 6),
    }
    return metrics


def train_model_from_splits(train_rows, valid_rows, test_rows, *, config):
    preprocessor = FeaturePreprocessor()
    preprocessor.fit(train_rows)

    x_train = preprocessor.transform(train_rows)
    y_train = preprocessor.labels(train_rows)
    x_valid = preprocessor.transform(valid_rows)
    y_valid = preprocessor.labels(valid_rows)
    x_test = preprocessor.transform(test_rows)
    y_test = preprocessor.labels(test_rows)

    hidden_dims = tuple(int(dim) for dim in config.get("hidden_dims", (32, 16)))
    model = NumpyMLPBinaryClassifier(
        input_dim=preprocessor.input_dim,
        hidden_dims=hidden_dims,
        seed=int(config.get("seed", 42)),
    )
    training_state = model.train(
        x_train,
        y_train,
        x_valid,
        y_valid,
        learning_rate=float(config.get("learning_rate", 0.01)),
        batch_size=int(config.get("batch_size", 16)),
        epochs=int(config.get("epochs", 120)),
        dropout_rate=float(config.get("dropout", 0.1)),
        patience=int(config.get("patience", 15)),
        seed=int(config.get("seed", 42)),
    )

    train_scores = model.predict_proba(x_train)
    valid_scores = model.predict_proba(x_valid)
    test_scores = model.predict_proba(x_test)

    metrics_report = {
        "train": evaluate_split(train_rows, y_train, train_scores),
        "valid": evaluate_split(valid_rows, y_valid, valid_scores),
        "test": evaluate_split(test_rows, y_test, test_scores),
        "training": {
            "best_epoch": int(training_state["best_epoch"]),
            "best_valid_auc": round(float(training_state["best_valid_auc"]), 6),
            "epochs_ran": int(len(training_state["history"])),
            "history": deepcopy(training_state["history"]),
        },
    }

    return {
        "model": model,
        "preprocessor": preprocessor,
        "metrics_report": metrics_report,
    }


def _sha256_file(path):
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def save_training_artifacts(*, output_dir, model_bundle, config, protocol=None, model_version="plan11b-mlp-v1"):
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    model = model_bundle["model"]
    preprocessor = model_bundle["preprocessor"]
    metrics_report = model_bundle["metrics_report"]

    weights_payload = {}
    for idx, weight in enumerate(model.weights):
        weights_payload[f"W{idx}"] = weight.astype(np.float64)
    for idx, bias in enumerate(model.biases):
        weights_payload[f"b{idx}"] = bias.astype(np.float64)

    weights_file = output_path / "model_weights.npz"
    np.savez(weights_file, **weights_payload)

    preprocessing_file = output_path / "preprocessing_config.json"
    preprocessing_file.write_text(
        json.dumps(preprocessor.to_dict(), ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    training_config_file = output_path / "training_config.json"
    training_config_file.write_text(
        json.dumps(config, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    metrics_file = output_path / "metrics_report.json"
    metrics_file.write_text(
        json.dumps(metrics_report, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    metadata = {
        "model_version": model_version,
        "model_family": "numpy-mlp-binary",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_dim": int(preprocessor.input_dim),
        "hidden_dims": list(model.hidden_dims),
        "dataset_protocol": protocol or {},
        "metrics_summary": {
            "test_auc": metrics_report["test"]["auc"],
            "test_f1": metrics_report["test"]["f1"],
            "test_recall_at_5": metrics_report["test"]["recall_at_5"],
            "test_ndcg_at_10": metrics_report["test"]["ndcg_at_10"],
        },
    }
    metadata_file = output_path / "model_metadata.json"
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    checksums = {
        "model_weights.npz": _sha256_file(weights_file),
        "preprocessing_config.json": _sha256_file(preprocessing_file),
        "training_config.json": _sha256_file(training_config_file),
        "metrics_report.json": _sha256_file(metrics_file),
        "model_metadata.json": _sha256_file(metadata_file),
    }
    checksum_lines = ["%s  %s" % (digest, name) for name, digest in sorted(checksums.items())]
    checksum_file = output_path / "artifact_checksum.sha256"
    checksum_file.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    return {
        "output_dir": str(output_path),
        "model_version": model_version,
        "checksums": checksums,
        "metrics_report": metrics_report,
    }
