from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def sigmoid(x):
    clipped = np.clip(x, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-clipped))


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


def classification_metrics(y_true, y_score, threshold=0.5):
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = (np.asarray(y_score, dtype=np.float64) >= threshold).astype(np.int64)
    if len(y_true) == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "auc": 0.5}

    y_true_bin = (y_true >= 0.5).astype(np.int64)
    tp = int(((y_true_bin == 1) & (y_pred == 1)).sum())
    tn = int(((y_true_bin == 0) & (y_pred == 0)).sum())
    fp = int(((y_true_bin == 0) & (y_pred == 1)).sum())
    fn = int(((y_true_bin == 1) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if precision + recall > 0 else 0.0
    accuracy = (tp + tn) / len(y_true_bin) if len(y_true_bin) else 0.0

    return {
        "accuracy": round(float(accuracy), 6),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
        "auc": round(float(auc_score(y_true, y_score)), 6),
    }


def sequence_batch_to_dense(batch, preprocess_config):
    action_ids = batch["action_ids"]
    product_ids = batch["product_ids"]
    category_ids = batch["category_ids"]
    time_delta = batch["time_delta_hours"]
    session_positions = batch["session_positions"]
    mask = batch["mask"]

    action_vocab_size = len(preprocess_config["action_vocab"])
    product_scale = max(1.0, float(preprocess_config.get("product_id_scale", 1.0)))
    category_scale = max(1.0, float(preprocess_config.get("category_id_scale", 1.0)))
    time_scale = max(1.0, float(preprocess_config.get("time_delta_hours_clip", 1.0)))
    pos_scale = max(1.0, float(preprocess_config.get("session_position_clip", 1.0)))

    sample_count, sequence_length = action_ids.shape
    dense = np.zeros((sample_count, sequence_length, action_vocab_size + 5), dtype=np.float64)

    for action_id in range(action_vocab_size):
        dense[:, :, action_id] = (action_ids == action_id).astype(np.float64)

    dense[:, :, action_vocab_size + 0] = product_ids / product_scale
    dense[:, :, action_vocab_size + 1] = category_ids / category_scale
    dense[:, :, action_vocab_size + 2] = time_delta / time_scale
    dense[:, :, action_vocab_size + 3] = session_positions / pos_scale
    dense[:, :, action_vocab_size + 4] = (product_ids > 0).astype(np.float64)
    dense = dense * mask[:, :, None]
    return dense


class BaseSequenceClassifier:
    def __init__(self, input_dim, hidden_dim=16, seed=42):
        self.input_dim = int(input_dim)
        self.hidden_dim = int(hidden_dim)
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

    def copy_state(self):
        return {
            key: np.array(value, copy=True)
            for key, value in self.__dict__.items()
            if isinstance(value, np.ndarray)
        }

    def load_state(self, state):
        for key, value in state.items():
            setattr(self, key, np.array(value, copy=True))

    def predict_proba(self, x, mask):
        outputs = []
        for sample_x, sample_mask in zip(x, mask):
            outputs.append(self.forward_single(sample_x, sample_mask)[0])
        return np.asarray(outputs, dtype=np.float64)

    def fit(self, train_x, train_mask, train_y, valid_x, valid_mask, valid_y, *, epochs=8, learning_rate=0.01):
        best_state = self.copy_state()
        best_f1 = -1.0
        history = []

        for epoch in range(1, max(1, int(epochs)) + 1):
            indices = self.rng.permutation(len(train_x))
            for idx in indices:
                self.train_single(train_x[idx], train_mask[idx], float(train_y[idx]), learning_rate)

            train_scores = self.predict_proba(train_x, train_mask)
            valid_scores = self.predict_proba(valid_x, valid_mask) if len(valid_x) else np.asarray([], dtype=np.float64)
            train_metrics = classification_metrics(train_y, train_scores)
            valid_metrics = classification_metrics(valid_y, valid_scores) if len(valid_y) else classification_metrics([], [])
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": round(binary_cross_entropy(train_y, train_scores), 6),
                    "valid_loss": round(binary_cross_entropy(valid_y, valid_scores), 6) if len(valid_y) else 0.0,
                    "train_f1": train_metrics["f1"],
                    "valid_f1": valid_metrics["f1"],
                    "valid_auc": valid_metrics["auc"],
                }
            )
            if valid_metrics["f1"] > best_f1:
                best_f1 = valid_metrics["f1"]
                best_state = self.copy_state()

        self.load_state(best_state)
        return history


class RNNBinaryClassifier(BaseSequenceClassifier):
    model_name = "rnn"

    def __init__(self, input_dim, hidden_dim=16, seed=42):
        super().__init__(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
        scale = math.sqrt(1.0 / max(1, input_dim))
        self.Wxh = self.rng.normal(0.0, scale, size=(input_dim, hidden_dim))
        self.Whh = self.rng.normal(0.0, scale, size=(hidden_dim, hidden_dim))
        self.bh = np.zeros((hidden_dim,), dtype=np.float64)
        self.Why = self.rng.normal(0.0, scale, size=(hidden_dim, 1))
        self.by = np.zeros((1,), dtype=np.float64)

    def forward_single(self, x, mask):
        h_prev = np.zeros((self.hidden_dim,), dtype=np.float64)
        states = []
        preacts = []
        for step_x, step_mask in zip(x, mask):
            if step_mask <= 0:
                states.append(np.array(h_prev, copy=True))
                preacts.append(None)
                continue
            z = step_x @ self.Wxh + h_prev @ self.Whh + self.bh
            h_prev = np.tanh(z)
            states.append(np.array(h_prev, copy=True))
            preacts.append(z)

        logits = float(states[-1] @ self.Why[:, 0] + self.by[0]) if len(states) else 0.0
        score = float(sigmoid(logits))
        cache = {"states": states, "preacts": preacts}
        return score, cache

    def train_single(self, x, mask, y_true, learning_rate):
        score, cache = self.forward_single(x, mask)
        states = cache["states"]
        preacts = cache["preacts"]
        if not states:
            return

        dlogit = score - y_true
        dWhy = np.outer(states[-1], np.asarray([dlogit]))
        dby = np.asarray([dlogit])

        dWxh = np.zeros_like(self.Wxh)
        dWhh = np.zeros_like(self.Whh)
        dbh = np.zeros_like(self.bh)

        dh_next = dlogit * self.Why[:, 0]
        prev_state = np.zeros((self.hidden_dim,), dtype=np.float64)
        for index in range(len(states) - 1, -1, -1):
            step_mask = mask[index]
            current_state = states[index]
            if index > 0:
                prev_state = states[index - 1]
            else:
                prev_state = np.zeros((self.hidden_dim,), dtype=np.float64)
            if step_mask <= 0 or preacts[index] is None:
                continue
            dz = dh_next * (1.0 - current_state ** 2)
            dWxh += np.outer(x[index], dz)
            dWhh += np.outer(prev_state, dz)
            dbh += dz
            dh_next = dz @ self.Whh.T

        self.Wxh -= learning_rate * dWxh
        self.Whh -= learning_rate * dWhh
        self.bh -= learning_rate * dbh
        self.Why -= learning_rate * dWhy
        self.by -= learning_rate * dby


class LSTMBinaryClassifier(BaseSequenceClassifier):
    model_name = "lstm"

    def __init__(self, input_dim, hidden_dim=16, seed=42):
        super().__init__(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
        scale = math.sqrt(1.0 / max(1, input_dim))
        self.W = self.rng.normal(0.0, scale, size=(input_dim + hidden_dim, hidden_dim * 4))
        self.b = np.zeros((hidden_dim * 4,), dtype=np.float64)
        self.Wy = self.rng.normal(0.0, scale, size=(hidden_dim, 1))
        self.by = np.zeros((1,), dtype=np.float64)

    def forward_single(self, x, mask):
        h = np.zeros((self.hidden_dim,), dtype=np.float64)
        c = np.zeros((self.hidden_dim,), dtype=np.float64)
        cache = []

        for step_x, step_mask in zip(x, mask):
            if step_mask <= 0:
                cache.append({"mask": 0, "h": np.array(h, copy=True), "c": np.array(c, copy=True)})
                continue
            concat = np.concatenate([step_x, h])
            gates = concat @ self.W + self.b
            i = sigmoid(gates[: self.hidden_dim])
            f = sigmoid(gates[self.hidden_dim : self.hidden_dim * 2])
            o = sigmoid(gates[self.hidden_dim * 2 : self.hidden_dim * 3])
            g = np.tanh(gates[self.hidden_dim * 3 :])
            prev_c = np.array(c, copy=True)
            prev_h = np.array(h, copy=True)
            c = f * c + i * g
            tanh_c = np.tanh(c)
            h = o * tanh_c
            cache.append(
                {
                    "mask": 1,
                    "concat": concat,
                    "i": i,
                    "f": f,
                    "o": o,
                    "g": g,
                    "prev_c": prev_c,
                    "prev_h": prev_h,
                    "c": np.array(c, copy=True),
                    "h": np.array(h, copy=True),
                    "tanh_c": tanh_c,
                }
            )

        logits = float(cache[-1]["h"] @ self.Wy[:, 0] + self.by[0]) if cache else 0.0
        score = float(sigmoid(logits))
        return score, cache

    def train_single(self, x, mask, y_true, learning_rate):
        score, cache = self.forward_single(x, mask)
        if not cache:
            return

        dlogit = score - y_true
        dWy = np.outer(cache[-1]["h"], np.asarray([dlogit]))
        dby = np.asarray([dlogit])
        dW = np.zeros_like(self.W)
        db = np.zeros_like(self.b)
        dh_next = dlogit * self.Wy[:, 0]
        dc_next = np.zeros((self.hidden_dim,), dtype=np.float64)

        for index in range(len(cache) - 1, -1, -1):
            step = cache[index]
            if step["mask"] <= 0:
                continue
            tanh_c = step["tanh_c"]
            o = step["o"]
            i = step["i"]
            f = step["f"]
            g = step["g"]
            prev_c = step["prev_c"]

            do = dh_next * tanh_c
            dc = dh_next * o * (1.0 - tanh_c ** 2) + dc_next
            di = dc * g
            dg = dc * i
            df = dc * prev_c
            dc_next = dc * f

            di_input = di * i * (1.0 - i)
            df_input = df * f * (1.0 - f)
            do_input = do * o * (1.0 - o)
            dg_input = dg * (1.0 - g ** 2)
            gate_grad = np.concatenate([di_input, df_input, do_input, dg_input])

            dW += np.outer(step["concat"], gate_grad)
            db += gate_grad
            dconcat = gate_grad @ self.W.T
            dh_next = dconcat[self.input_dim :]

        self.W -= learning_rate * dW
        self.b -= learning_rate * db
        self.Wy -= learning_rate * dWy
        self.by -= learning_rate * dby


class BiLSTMBinaryClassifier(BaseSequenceClassifier):
    model_name = "bilstm"

    def __init__(self, input_dim, hidden_dim=16, seed=42):
        super().__init__(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
        self.forward_lstm = LSTMBinaryClassifier(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
        self.backward_lstm = LSTMBinaryClassifier(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed + 1)
        scale = math.sqrt(1.0 / max(1, hidden_dim * 2))
        self.Wy = self.rng.normal(0.0, scale, size=(hidden_dim * 2, 1))
        self.by = np.zeros((1,), dtype=np.float64)

    def copy_state(self):
        return {
            "forward": self.forward_lstm.copy_state(),
            "backward": self.backward_lstm.copy_state(),
            "Wy": np.array(self.Wy, copy=True),
            "by": np.array(self.by, copy=True),
        }

    def load_state(self, state):
        self.forward_lstm.load_state(state["forward"])
        self.backward_lstm.load_state(state["backward"])
        self.Wy = np.array(state["Wy"], copy=True)
        self.by = np.array(state["by"], copy=True)

    def forward_single(self, x, mask):
        _, forward_cache = self.forward_lstm.forward_single(x, mask)
        reversed_x = x[::-1]
        reversed_mask = mask[::-1]
        _, backward_cache = self.backward_lstm.forward_single(reversed_x, reversed_mask)
        h_forward = forward_cache[-1]["h"] if forward_cache else np.zeros((self.hidden_dim,), dtype=np.float64)
        h_backward = backward_cache[-1]["h"] if backward_cache else np.zeros((self.hidden_dim,), dtype=np.float64)
        h_concat = np.concatenate([h_forward, h_backward])
        logits = float(h_concat @ self.Wy[:, 0] + self.by[0])
        score = float(sigmoid(logits))
        return score, {"forward": forward_cache, "backward": backward_cache, "h_concat": h_concat}

    def train_single(self, x, mask, y_true, learning_rate):
        score, cache = self.forward_single(x, mask)
        dlogit = score - y_true
        dWy = np.outer(cache["h_concat"], np.asarray([dlogit]))
        dby = np.asarray([dlogit])
        dh = dlogit * self.Wy[:, 0]

        self.forward_lstm.train_single(x, mask, y_true=0.0, learning_rate=0.0)
        self.backward_lstm.train_single(x[::-1], mask[::-1], y_true=0.0, learning_rate=0.0)

        self.Wy -= learning_rate * dWy
        self.by -= learning_rate * dby

        self._backprop_lstm(self.forward_lstm, x, mask, dh[: self.hidden_dim], learning_rate)
        self._backprop_lstm(self.backward_lstm, x[::-1], mask[::-1], dh[self.hidden_dim :], learning_rate)

    def _backprop_lstm(self, model, x, mask, external_dh_last, learning_rate):
        score, cache = model.forward_single(x, mask)
        if not cache:
            return
        dW = np.zeros_like(model.W)
        db = np.zeros_like(model.b)
        dh_next = np.array(external_dh_last, copy=True)
        dc_next = np.zeros((model.hidden_dim,), dtype=np.float64)

        for index in range(len(cache) - 1, -1, -1):
            step = cache[index]
            if step["mask"] <= 0:
                continue
            tanh_c = step["tanh_c"]
            o = step["o"]
            i = step["i"]
            f = step["f"]
            g = step["g"]
            prev_c = step["prev_c"]

            do = dh_next * tanh_c
            dc = dh_next * o * (1.0 - tanh_c ** 2) + dc_next
            di = dc * g
            dg = dc * i
            df = dc * prev_c
            dc_next = dc * f

            di_input = di * i * (1.0 - i)
            df_input = df * f * (1.0 - f)
            do_input = do * o * (1.0 - o)
            dg_input = dg * (1.0 - g ** 2)
            gate_grad = np.concatenate([di_input, df_input, do_input, dg_input])

            dW += np.outer(step["concat"], gate_grad)
            db += gate_grad
            dconcat = gate_grad @ model.W.T
            dh_next = dconcat[model.input_dim :]

        model.W -= learning_rate * dW
        model.b -= learning_rate * db


def _write_line_chart_svg(path, history, key_left, key_right, title):
    width = 720
    height = 320
    margin = 40
    values = [row[key_left] for row in history] + [row[key_right] for row in history]
    if not values:
        values = [0.0]
    min_v = min(values)
    max_v = max(values)
    if abs(max_v - min_v) < 1e-9:
        max_v = min_v + 1.0

    def project(index, value):
        x = margin + index * (width - 2 * margin) / max(1, len(history) - 1)
        y = height - margin - ((value - min_v) / (max_v - min_v)) * (height - 2 * margin)
        return x, y

    left_points = " ".join("%.1f,%.1f" % project(idx, row[key_left]) for idx, row in enumerate(history))
    right_points = " ".join("%.1f,%.1f" % project(idx, row[key_right]) for idx, row in enumerate(history))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="{width}" height="{height}" fill="#fffdf7"/>
<text x="{margin}" y="24" font-size="18" font-family="Arial" fill="#1c1c1c">{title}</text>
<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#666"/>
<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#666"/>
<polyline fill="none" stroke="#005f73" stroke-width="3" points="{left_points}"/>
<polyline fill="none" stroke="#ca6702" stroke-width="3" points="{right_points}"/>
<text x="{width - 170}" y="{margin}" font-size="12" font-family="Arial" fill="#005f73">{key_left}</text>
<text x="{width - 170}" y="{margin + 18}" font-size="12" font-family="Arial" fill="#ca6702">{key_right}</text>
</svg>"""
    Path(path).write_text(svg, encoding="utf-8")


def load_sequence_npz(path):
    payload = np.load(Path(path), allow_pickle=False)
    return {key: payload[key] for key in payload.files}


def train_model(train_payload, valid_payload, test_payload, preprocess_config, *, model_type, hidden_dim=16, epochs=8, learning_rate=0.01, seed=42):
    train_x = sequence_batch_to_dense(train_payload, preprocess_config)
    valid_x = sequence_batch_to_dense(valid_payload, preprocess_config)
    test_x = sequence_batch_to_dense(test_payload, preprocess_config)
    train_mask = train_payload["mask"]
    valid_mask = valid_payload["mask"]
    test_mask = test_payload["mask"]
    train_y = train_payload["labels"]
    valid_y = valid_payload["labels"]
    test_y = test_payload["labels"]
    input_dim = train_x.shape[-1]

    if model_type == "rnn":
        model = RNNBinaryClassifier(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
    elif model_type == "lstm":
        model = LSTMBinaryClassifier(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
    elif model_type == "bilstm":
        model = BiLSTMBinaryClassifier(input_dim=input_dim, hidden_dim=hidden_dim, seed=seed)
    else:
        raise ValueError("Unsupported model_type: %s" % model_type)

    history = model.fit(
        train_x,
        train_mask,
        train_y,
        valid_x,
        valid_mask,
        valid_y,
        epochs=epochs,
        learning_rate=learning_rate,
    )

    train_scores = model.predict_proba(train_x, train_mask)
    valid_scores = model.predict_proba(valid_x, valid_mask)
    test_scores = model.predict_proba(test_x, test_mask)

    metrics = {
        "train": classification_metrics(train_y, train_scores),
        "valid": classification_metrics(valid_y, valid_scores),
        "test": classification_metrics(test_y, test_scores),
        "training": {
            "epochs_ran": len(history),
            "history": history,
        },
    }
    return model, metrics


def save_model_artifacts(output_dir, *, model_type, model, metrics, config):
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    state = model.copy_state()
    arrays = {}
    for key, value in state.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                for inner_key, inner_val in subvalue.items():
                    arrays[f"{key}_{subkey}_{inner_key}"] = inner_val
        else:
            arrays[key] = value
    np.savez(output_path / "weights.npz", **arrays)
    (output_path / "metrics_report.json").write_text(
        json.dumps(metrics, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_path / "training_config.json").write_text(
        json.dumps(config, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    history = metrics["training"]["history"]
    _write_line_chart_svg(output_path / "loss_curve.svg", history, "train_loss", "valid_loss", f"{model_type.upper()} loss")
    _write_line_chart_svg(output_path / "f1_curve.svg", history, "train_f1", "valid_f1", f"{model_type.upper()} F1")


def select_best_model(model_reports):
    ordered = sorted(
        model_reports,
        key=lambda row: (-row["metrics"]["valid"]["f1"], -row["metrics"]["valid"]["auc"], row["model_type"]),
    )
    return ordered[0]


def write_comparison_report(output_dir, model_reports, best_report):
    output_path = Path(output_dir).resolve()
    lines = [
        "# Exercise Sequence Model Comparison",
        "",
        "Selection rule: highest validation F1, then validation AUC, then model name.",
        "",
        "| Model | Valid Accuracy | Valid Precision | Valid Recall | Valid F1 | Valid AUC | Test F1 | Test AUC |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in model_reports:
        valid = row["metrics"]["valid"]
        test = row["metrics"]["test"]
        lines.append(
            "| %s | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f | %.4f |"
            % (
                row["model_type"],
                valid["accuracy"],
                valid["precision"],
                valid["recall"],
                valid["f1"],
                valid["auc"],
                test["f1"],
                test["auc"],
            )
        )
    lines.extend(
        [
            "",
            "## model_best",
            "",
            "Selected model: `%s`" % best_report["model_type"],
            "",
            "Reason: it achieved the highest validation F1 under the locked comparison rule.",
        ]
    )
    (output_path / "comparison_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_best_model(output_dir, best_model_type):
    output_path = Path(output_dir).resolve()
    best_src = output_path / best_model_type
    best_dst = output_path / "model_best"
    if best_dst.exists():
        shutil.rmtree(best_dst)
    shutil.copytree(best_src, best_dst)

