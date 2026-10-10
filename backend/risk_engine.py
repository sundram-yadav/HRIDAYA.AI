from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List


LEAKAGE_COLUMNS = {"Cath", "CAD", "LAD", "LCX", "RCA", "cad", "lad", "lcx", "rca"}


FEATURE_SCHEMA: List[Dict[str, Any]] = [
    {"name": "age", "label": "Age", "group": "Demographics", "type": "number", "min": 25, "max": 90, "default": 54, "unit": "years"},
    {"name": "sex", "label": "Sex", "group": "Demographics", "type": "category", "default": "male", "allowed_values": ["female", "male"]},
    {"name": "typical_chest_pain", "label": "Typical chest pain", "group": "Symptoms", "type": "boolean", "default": False},
    {"name": "dyspnea", "label": "Dyspnea", "group": "Symptoms", "type": "boolean", "default": False},
    {"name": "diabetes", "label": "Diabetes", "group": "Risk factors", "type": "boolean", "default": False},
    {"name": "hypertension", "label": "Hypertension", "group": "Risk factors", "type": "boolean", "default": False},
    {"name": "smoking", "label": "Smoking", "group": "Risk factors", "type": "boolean", "default": False},
    {"name": "bp_sys", "label": "Systolic BP", "group": "Vitals", "type": "number", "min": 90, "max": 210, "default": 130, "unit": "mmHg"},
    {"name": "bp_dia", "label": "Diastolic BP", "group": "Vitals", "type": "number", "min": 50, "max": 130, "default": 82, "unit": "mmHg"},
    {"name": "pulse", "label": "Pulse rate", "group": "Vitals", "type": "number", "min": 45, "max": 130, "default": 76, "unit": "bpm"},
    {"name": "bmi", "label": "BMI", "group": "Vitals", "type": "number", "min": 17, "max": 42, "default": 26, "unit": "kg/m2"},
    {"name": "cholesterol", "label": "Total cholesterol", "group": "Labs", "type": "number", "min": 110, "max": 360, "default": 190, "unit": "mg/dL"},
    {"name": "ldl", "label": "LDL", "group": "Labs", "type": "number", "min": 45, "max": 240, "default": 112, "unit": "mg/dL"},
    {"name": "hdl", "label": "HDL", "group": "Labs", "type": "number", "min": 20, "max": 95, "default": 45, "unit": "mg/dL"},
    {"name": "fbs", "label": "Fasting blood sugar", "group": "Labs", "type": "number", "min": 70, "max": 260, "default": 104, "unit": "mg/dL"},
    {"name": "region_rwma", "label": "Region with RWMA", "group": "Echo", "type": "category", "default": "none", "allowed_values": ["none", "anterior", "inferior", "lateral", "multiple"]},
]


METRICS: Dict[str, Any] = {
    "mode": "demo",
    "note": "Validation metrics are populated after training with the local dataset.",
    "targets": {
        "cad": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0},
        "lad": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0},
        "lcx": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0},
        "rca": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0},
    },
}


SAMPLE_PATIENTS: List[Dict[str, Any]] = [
    {
        "id": "sample-low",
        "label": "Lower risk demo patient",
        "patient": {
            "age": 42,
            "sex": "female",
            "typical_chest_pain": False,
            "dyspnea": False,
            "diabetes": False,
            "hypertension": False,
            "smoking": False,
            "bp_sys": 118,
            "bp_dia": 76,
            "pulse": 72,
            "bmi": 23,
            "cholesterol": 168,
            "ldl": 88,
            "hdl": 58,
            "fbs": 92,
            "region_rwma": "none",
        },
    },
    {
        "id": "sample-medium",
        "label": "Intermediate risk demo patient",
        "patient": {
            "age": 58,
            "sex": "male",
            "typical_chest_pain": True,
            "dyspnea": False,
            "diabetes": False,
            "hypertension": True,
            "smoking": False,
            "bp_sys": 148,
            "bp_dia": 88,
            "pulse": 82,
            "bmi": 28,
            "cholesterol": 218,
            "ldl": 142,
            "hdl": 40,
            "fbs": 111,
            "region_rwma": "anterior",
        },
    },
    {
        "id": "sample-high",
        "label": "Higher risk demo patient",
        "patient": {
            "age": 68,
            "sex": "male",
            "typical_chest_pain": True,
            "dyspnea": True,
            "diabetes": True,
            "hypertension": True,
            "smoking": True,
            "bp_sys": 166,
            "bp_dia": 94,
            "pulse": 96,
            "bmi": 32,
            "cholesterol": 260,
            "ldl": 174,
            "hdl": 34,
            "fbs": 158,
            "region_rwma": "multiple",
        },
    },
]


@dataclass(frozen=True)
class Contribution:
    feature: str
    label: str
    value: Any
    impact: float
    direction: str


def _defaults() -> Dict[str, Any]:
    return {feature["name"]: feature["default"] for feature in FEATURE_SCHEMA}


def normalize_patient(patient: Dict[str, Any]) -> Dict[str, Any]:
    forbidden = LEAKAGE_COLUMNS.intersection(patient.keys())
    if forbidden:
        raise ValueError(f"Input contains leakage columns: {sorted(forbidden)}")
    merged = _defaults()
    merged.update({key: value for key, value in patient.items() if key in merged})
    return merged


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _score(patient: Dict[str, Any], target: str) -> tuple[float, List[Contribution]]:
    p = normalize_patient(patient)
    label_by_name = {item["name"]: item["label"] for item in FEATURE_SCHEMA}
    weights = {
        "cad": {"base": -3.1, "age": 0.042, "male": 0.38, "pain": 0.85, "dyspnea": 0.3, "diabetes": 0.48, "htn": 0.34, "smoking": 0.32, "sys": 0.016, "bmi": 0.035, "ldl": 0.009, "hdl": -0.015, "fbs": 0.006, "rwma": 0.35},
        "lad": {"base": -3.4, "age": 0.043, "male": 0.32, "pain": 0.92, "dyspnea": 0.18, "diabetes": 0.38, "htn": 0.28, "smoking": 0.28, "sys": 0.014, "bmi": 0.026, "ldl": 0.01, "hdl": -0.012, "fbs": 0.005, "rwma": 0.55},
        "lcx": {"base": -3.25, "age": 0.036, "male": 0.26, "pain": 0.62, "dyspnea": 0.2, "diabetes": 0.4, "htn": 0.25, "smoking": 0.38, "sys": 0.011, "bmi": 0.03, "ldl": 0.008, "hdl": -0.01, "fbs": 0.006, "rwma": 0.42},
        "rca": {"base": -3.15, "age": 0.038, "male": 0.3, "pain": 0.66, "dyspnea": 0.28, "diabetes": 0.35, "htn": 0.3, "smoking": 0.52, "sys": 0.012, "bmi": 0.028, "ldl": 0.007, "hdl": -0.01, "fbs": 0.006, "rwma": 0.48},
    }[target]

    impacts = {
        "age": weights["age"] * (float(p["age"]) - 50),
        "sex": weights["male"] if p["sex"] == "male" else 0,
        "typical_chest_pain": weights["pain"] if p["typical_chest_pain"] else 0,
        "dyspnea": weights["dyspnea"] if p["dyspnea"] else 0,
        "diabetes": weights["diabetes"] if p["diabetes"] else 0,
        "hypertension": weights["htn"] if p["hypertension"] else 0,
        "smoking": weights["smoking"] if p["smoking"] else 0,
        "bp_sys": weights["sys"] * (float(p["bp_sys"]) - 120),
        "bmi": weights["bmi"] * (float(p["bmi"]) - 24),
        "ldl": weights["ldl"] * (float(p["ldl"]) - 100),
        "hdl": weights["hdl"] * (float(p["hdl"]) - 45),
        "fbs": weights["fbs"] * (float(p["fbs"]) - 95),
        "region_rwma": weights["rwma"] if p["region_rwma"] != "none" else 0,
    }
    raw = weights["base"] + sum(impacts.values())
    contributions = [
        Contribution(name, label_by_name[name], p[name], round(value, 3), "increases" if value >= 0 else "decreases")
        for name, value in impacts.items()
    ]
    return raw, sorted(contributions, key=lambda item: abs(item.impact), reverse=True)


def predict_all(patient: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_patient(patient)
    targets = {}
    for target in ("cad", "lad", "lcx", "rca"):
        raw, _ = _score(normalized, target)
        probability = _sigmoid(raw)
        width = min(0.24, 0.09 + abs(probability - 0.5) * 0.12)
        targets[target] = {
            "probability": round(probability, 3),
            "ci_low": round(max(0, probability - width), 3),
            "ci_high": round(min(1, probability + width), 3),
            "risk_level": "high" if probability >= 0.7 else "moderate" if probability >= 0.4 else "low",
            "low_confidence": width > 0.18,
        }
    return {
        "mode": "demo",
        "disclaimer": "For decision support / educational purposes only. Not a substitute for formal diagnostic imaging.",
        "patient": normalized,
        "targets": targets,
    }


def explain_patient(patient: Dict[str, Any], target: str) -> Dict[str, Any]:
    normalized = normalize_patient(patient)
    raw, contributions = _score(normalized, target)
    top = contributions[:8]
    return {
        "target": target,
        "probability": round(_sigmoid(raw), 3),
        "note": "Explanation values are produced by the current risk engine. Dataset-trained SHAP values are used after model training.",
        "contributions": [item.__dict__ for item in top],
        "sentences": [
            f"{item.label} ({item.value}) {item.direction} {target.upper()} risk."
            for item in top[:4]
        ],
    }


def suggest_counterfactual(patient: Dict[str, Any], target: str) -> Dict[str, Any]:
    current = normalize_patient(patient)
    before = predict_all(current)["targets"][target]["probability"]
    adjusted = dict(current)
    adjusted["bp_sys"] = max(120, float(adjusted["bp_sys"]) - 12)
    adjusted["ldl"] = max(90, float(adjusted["ldl"]) - 25)
    adjusted["bmi"] = max(24, float(adjusted["bmi"]) - 2)
    adjusted["fbs"] = max(95, float(adjusted["fbs"]) - 15)
    after = predict_all(adjusted)["targets"][target]["probability"]
    return {
        "target": target,
        "before": before,
        "after": after,
        "delta": round(after - before, 3),
        "suggestions": [
            "Illustrative what-if only; not medical advice.",
            "Lower systolic BP toward 120 mmHg if clinically appropriate.",
            "Lower LDL and improve metabolic markers under clinician guidance.",
            "Reduce BMI modestly when weight is a relevant modifiable factor.",
        ],
        "patient": adjusted,
    }
