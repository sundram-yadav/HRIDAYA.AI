"""Load saved artifacts and score a patient dict."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ml.leakage import LEAKAGE_COLUMNS, assert_no_leakage
from ml.preprocess import vectorize_patient

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
DISCLAIMER = (
    "For decision support / educational purposes only. "
    "Not a substitute for formal diagnostic imaging."
)
MODIFIABLE = ["BP", "LDL", "HDL", "TG", "FBS", "Weight", "BMI"]


def load_artifacts() -> dict[str, Any]:
    registry_path = MODELS_DIR / "registry.joblib"
    if not registry_path.exists():
        raise FileNotFoundError("models/registry.joblib missing. Run python -m ml.train first.")
    registry = joblib.load(registry_path)
    schema = json.loads((MODELS_DIR / "feature_schema.json").read_text(encoding="utf-8"))
    metrics = json.loads((MODELS_DIR / "metrics.json").read_text(encoding="utf-8"))
    samples = json.loads((MODELS_DIR / "sample_patients.json").read_text(encoding="utf-8"))
    return {"registry": registry, "schema": schema, "metrics": metrics, "samples": samples}


def _ci_from_models(models: list, X) -> tuple[float, float, float]:
    features = X.to_numpy(dtype=float)
    probs = []
    for model in models:
        if hasattr(model, "predict_proba"):
            probs.append(float(model.predict_proba(features)[0, 1]))
        else:
            probs.append(float(model.predict(features)[0]))
    arr = np.asarray(probs, dtype=float)
    mean = float(arr.mean())
    if len(arr) == 1:
        return mean, max(0.0, mean - 0.08), min(1.0, mean + 0.08)
    low = float(np.percentile(arr, 2.5))
    high = float(np.percentile(arr, 97.5))
    return mean, max(0.0, low), min(1.0, high)


def predict_with_ci(patient: dict, target: str, artifacts: dict | None = None) -> dict[str, Any]:
    artifacts = artifacts or load_artifacts()
    assert_no_leakage(patient.keys())
    X = vectorize_patient(patient, artifacts["schema"])
    pack = artifacts["registry"]["targets"][target]
    mean, low, high = _ci_from_models(pack["ensemble_models"], X)
    primary = pack["model"]
    if hasattr(primary, "predict_proba"):
        mean = float(primary.predict_proba(X.to_numpy(dtype=float))[0, 1])
    low = min(low, mean)
    high = max(high, mean)
    width = high - low
    return {
        "probability": round(mean, 4),
        "ci_low": round(low, 4),
        "ci_high": round(high, 4),
        "risk_level": "high" if mean >= 0.7 else "moderate" if mean >= 0.4 else "low",
        "low_confidence": bool(width >= 0.25),
        "positive": bool(mean >= 0.5),
    }


def predict_all(patient_dict: dict, artifacts: dict | None = None) -> dict[str, Any]:
    artifacts = artifacts or load_artifacts()
    forbidden = set(patient_dict) & set(LEAKAGE_COLUMNS)
    if forbidden:
        raise ValueError(f"Input contains leakage columns: {sorted(forbidden)}")
    assert_no_leakage(patient_dict.keys())
    targets = {name: predict_with_ci(patient_dict, name, artifacts) for name in ("cad", "lad", "lcx", "rca")}
    return {
        "mode": "trained",
        "disclaimer": DISCLAIMER,
        "targets": targets,
    }


def explain_patient(patient: dict, target: str, artifacts: dict | None = None, top_k: int = 8) -> dict[str, Any]:
    artifacts = artifacts or load_artifacts()
    X = vectorize_patient(patient, artifacts["schema"])
    pack = artifacts["registry"]["targets"][target]
    feature_names = list(X.columns)
    shap_row = _shap_row(pack["model"], artifacts["registry"]["background"], X)
    order = np.argsort(np.abs(shap_row))[::-1][:top_k]
    contributions = []
    schema_by = {item["name"]: item for item in artifacts["schema"]["features"]}
    for idx in order:
        name = feature_names[idx]
        value = X.iloc[0, idx]
        shap_v = float(shap_row[idx])
        meta = schema_by.get(name, {})
        contributions.append(
            {
                "feature": name,
                "label": meta.get("label", name),
                "value": _pretty_value(name, patient, value, meta),
                "shap": round(shap_v, 4),
                "direction": "increases" if shap_v >= 0 else "decreases",
            }
        )
    pred = predict_with_ci(patient, target, artifacts)
    sentences = [
        f"{item['label']} ({item['value']}) {item['direction']} {target.upper()} risk."
        for item in contributions[:5]
    ]
    return {
        "target": target,
        "probability": pred["probability"],
        "contributions": contributions,
        "sentences": sentences,
        "rwma_note": "Region with RWMA is a clinical hint, not anatomical evidence.",
    }


def suggest_counterfactual(patient: dict, target: str, artifacts: dict | None = None) -> dict[str, Any]:
    """Illustrative what-if: smallest greedy changes on modifiable labs/vitals. Not medical advice."""
    artifacts = artifacts or load_artifacts()
    schema_by = {item["name"]: item for item in artifacts["schema"]["features"]}
    current = dict(patient)
    before = predict_with_ci(current, target, artifacts)["probability"]
    adjusted = dict(current)
    steps = []
    for _ in range(24):
        prob = predict_with_ci(adjusted, target, artifacts)["probability"]
        if prob < 0.5:
            break
        best = None
        for feat in MODIFIABLE:
            if feat not in schema_by:
                continue
            meta = schema_by[feat]
            old = float(adjusted.get(feat, meta["default"]))
            lo = float(meta.get("min", old))
            hi = float(meta.get("max", old))
            if feat == "HDL":
                trial = min(hi, old + max(2.0, (hi - lo) * 0.04))
            else:
                trial = max(lo, old - max(2.0, (hi - lo) * 0.04))
            if abs(trial - old) < 1e-6:
                continue
            trial_patient = dict(adjusted)
            trial_patient[feat] = trial
            if feat == "Weight" and "Length" in adjusted:
                length_m = float(adjusted["Length"]) / 100.0
                trial_patient["BMI"] = trial / (length_m ** 2)
            new_p = predict_with_ci(trial_patient, target, artifacts)["probability"]
            gain = prob - new_p
            if best is None or gain > best[0]:
                best = (gain, feat, trial, new_p, old)
        if best is None or best[0] <= 1e-4:
            break
        _, feat, trial, new_p, old = best
        adjusted[feat] = trial
        if feat == "Weight" and "Length" in adjusted:
            length_m = float(adjusted["Length"]) / 100.0
            adjusted["BMI"] = trial / (length_m ** 2)
        steps.append({"feature": feat, "from": round(old, 2), "to": round(float(trial), 2)})
    after = predict_with_ci(adjusted, target, artifacts)["probability"]
    return {
        "target": target,
        "before": round(before, 4),
        "after": round(after, 4),
        "delta": round(after - before, 4),
        "disclaimer": "Illustrative what-if, not medical advice.",
        "steps": steps,
        "patient": adjusted,
        "suggestions": [
            "Illustrative what-if, not medical advice.",
            "Changes are limited to a few modifiable vitals/labs already in the form.",
        ],
    }


def _shap_row(model, background, X) -> np.ndarray:
    import shap

    bg = background[: min(24, len(background))]

    def _proba(data, m=model):
        return m.predict_proba(np.asarray(data, dtype=float))[:, 1]

    explainer = shap.Explainer(_proba, bg, algorithm="permutation", seed=42)
    explanation = explainer(np.asarray(X, dtype=float), max_evals=2 * X.shape[1] + 1)
    values = np.asarray(explanation.values, dtype=float)
    if values.ndim >= 2:
        return values[0]
    return values.reshape(-1)


def _pretty_value(name: str, patient: dict, encoded: float, meta: dict) -> Any:
    if name in patient:
        return patient[name]
    if meta.get("type") == "boolean":
        return bool(encoded)
    if abs(encoded - round(encoded)) < 1e-6:
        return int(round(encoded))
    return round(float(encoded), 2)
