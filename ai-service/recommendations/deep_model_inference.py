import json
import logging
from pathlib import Path

import numpy as np
from django.conf import settings

from .deep_model_training import FeaturePreprocessor

logger = logging.getLogger(__name__)


class DeepModelRuntime:
    def __init__(self, *, enabled=None, artifact_dir=None, alpha=None, score_clip_min=None, score_clip_max=None):
        self.enabled = bool(getattr(settings, "DEEP_MODEL_ENABLED", True) if enabled is None else enabled)
        configured_dir = artifact_dir or getattr(settings, "DEEP_MODEL_ARTIFACT_DIR", Path(settings.BASE_DIR) / "artifacts" / "deep_model" / "11b")
        self.artifact_dir = Path(configured_dir).resolve()

        configured_alpha = getattr(settings, "DEEP_MODEL_SCORE_ALPHA", 0.35) if alpha is None else alpha
        self.alpha = max(0.0, float(configured_alpha))

        configured_min = getattr(settings, "DEEP_MODEL_SCORE_CLIP_MIN", 0.0) if score_clip_min is None else score_clip_min
        configured_max = getattr(settings, "DEEP_MODEL_SCORE_CLIP_MAX", 1.0) if score_clip_max is None else score_clip_max
        self.score_clip_min = float(configured_min)
        self.score_clip_max = float(configured_max)
        if self.score_clip_min > self.score_clip_max:
            self.score_clip_min, self.score_clip_max = self.score_clip_max, self.score_clip_min

        self._load_attempted = False
        self._loaded = False
        self._load_error = ""
        self._model_version = "unknown"
        self._preprocessor = None
        self._weights = []
        self._biases = []

    def status(self):
        self._ensure_loaded()
        fallback_mode = "deep-model" if self._loaded else "heuristic-only"
        if not self.enabled:
            fallback_mode = "heuristic-only-disabled"
        return {
            "enabled": bool(self.enabled),
            "loaded": bool(self._loaded),
            "model_version": self._model_version,
            "artifact_dir": str(self.artifact_dir),
            "alpha": float(self.alpha),
            "score_clip": {
                "min": float(self.score_clip_min),
                "max": float(self.score_clip_max),
            },
            "fallback_mode": fallback_mode,
            "error": None if self._loaded else (self._load_error or None),
        }

    def score_candidates(self, feature_rows):
        status = self.status()
        if not feature_rows:
            return {
                "applied": False,
                "scores": [],
                "model_version": status["model_version"],
                "fallback_mode": status["fallback_mode"],
                "error": None,
            }

        if not status["enabled"]:
            return {
                "applied": False,
                "scores": [],
                "model_version": status["model_version"],
                "fallback_mode": "heuristic-only-disabled",
                "error": None,
            }

        if not status["loaded"]:
            return {
                "applied": False,
                "scores": [],
                "model_version": status["model_version"],
                "fallback_mode": "heuristic-only-model-unavailable",
                "error": status.get("error"),
            }

        try:
            matrix = self._preprocessor.transform(feature_rows)
            raw_scores = self._predict_scores(matrix)
            clipped = np.clip(raw_scores, self.score_clip_min, self.score_clip_max).astype(np.float64)
            return {
                "applied": True,
                "scores": [float(score) for score in clipped.tolist()],
                "model_version": status["model_version"],
                "fallback_mode": "deep-model",
                "error": None,
            }
        except Exception as exc:
            logger.exception("Deep model inference failed: %s", exc)
            return {
                "applied": False,
                "scores": [],
                "model_version": status["model_version"],
                "fallback_mode": "heuristic-only-inference-error",
                "error": str(exc),
            }

    def _ensure_loaded(self):
        if self._load_attempted:
            return
        self._load_attempted = True

        if not self.enabled:
            self._load_error = "Deep model runtime is disabled by config."
            return

        try:
            metadata = self._read_json(self.artifact_dir / "model_metadata.json")
            preprocessing_config = self._read_json(self.artifact_dir / "preprocessing_config.json")
            weights_file = self.artifact_dir / "model_weights.npz"
            if not weights_file.exists():
                raise FileNotFoundError("Missing model_weights.npz")

            self._model_version = str(metadata.get("model_version") or "unknown")
            self._preprocessor = self._load_preprocessor(preprocessing_config)
            self._weights, self._biases = self._load_weights(weights_file)
            self._loaded = True
        except Exception as exc:
            self._loaded = False
            self._load_error = str(exc)
            logger.warning("Deep model artifact load failed: %s", exc)

    def _predict_scores(self, matrix):
        current = np.asarray(matrix, dtype=np.float64)
        for layer_idx in range(len(self._weights) - 1):
            current = np.maximum((current @ self._weights[layer_idx]) + self._biases[layer_idx], 0.0)

        logits = (current @ self._weights[-1]) + self._biases[-1]
        scores = 1.0 / (1.0 + np.exp(-np.clip(logits, -35.0, 35.0)))
        return scores.reshape(-1)

    def _load_preprocessor(self, config):
        preprocessor = FeaturePreprocessor(
            numeric_fields=list(config.get("numeric_fields", [])),
            categorical_fields=list(config.get("categorical_fields", [])),
        )
        preprocessor.numeric_means = {
            str(field): float(value)
            for field, value in (config.get("numeric_means") or {}).items()
        }
        preprocessor.numeric_stds = {
            str(field): (float(value) if abs(float(value)) >= 1e-9 else 1.0)
            for field, value in (config.get("numeric_stds") or {}).items()
        }
        preprocessor.categorical_vocab = {
            str(field): {
                str(token): int(index)
                for token, index in (vocab or {}).items()
            }
            for field, vocab in (config.get("categorical_vocab") or {}).items()
        }
        preprocessor.categorical_offsets = {
            str(field): int(offset)
            for field, offset in (config.get("categorical_offsets") or {}).items()
        }
        preprocessor.input_dim = int(config.get("input_dim") or 0)
        if preprocessor.input_dim <= 0:
            raise ValueError("Invalid preprocessing config: input_dim must be > 0")
        return preprocessor

    def _load_weights(self, weights_path):
        payload = np.load(weights_path)

        layer_ids = sorted(
            int(name[1:])
            for name in payload.files
            if name.startswith("W") and name[1:].isdigit()
        )
        if not layer_ids:
            raise ValueError("No weight matrices found in model_weights.npz")

        weights = []
        biases = []
        for layer_id in layer_ids:
            w_key = f"W{layer_id}"
            b_key = f"b{layer_id}"
            if b_key not in payload.files:
                raise ValueError(f"Missing bias vector for layer {layer_id}")
            weights.append(np.asarray(payload[w_key], dtype=np.float64))
            biases.append(np.asarray(payload[b_key], dtype=np.float64))

        return weights, biases

    def _read_json(self, path):
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError("Missing artifact file: %s" % file_path.name)
        return json.loads(file_path.read_text(encoding="utf-8"))
