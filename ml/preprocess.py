"""Clean the Z-Alizadeh Sani extension table and build a leakage-safe schema."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml.leakage import LEAKAGE_COLUMNS, assert_no_leakage, clean_column_name

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
SEED = 42

DROP_CONSTANT = {"Exertional_CP"}  # observed all-N in the xlsx; not a target

FEATURE_META = {
    "Age": {"label": "Age", "group": "Demographics", "unit": "years", "type": "number"},
    "Weight": {"label": "Weight", "group": "Demographics", "unit": "kg", "type": "number"},
    "Length": {"label": "Height", "group": "Demographics", "unit": "cm", "type": "number"},
    "Sex": {"label": "Sex", "group": "Demographics", "unit": None, "type": "category"},
    "BMI": {"label": "BMI", "group": "Demographics", "unit": "kg/m2", "type": "number"},
    "DM": {"label": "Diabetes mellitus", "group": "Risk factors", "unit": None, "type": "boolean"},
    "HTN": {"label": "Hypertension", "group": "Risk factors", "unit": None, "type": "boolean"},
    "Current_Smoker": {"label": "Current smoker", "group": "Risk factors", "unit": None, "type": "boolean"},
    "EX_Smoker": {"label": "Ex-smoker", "group": "Risk factors", "unit": None, "type": "boolean"},
    "FH": {"label": "Family history of CAD", "group": "Risk factors", "unit": None, "type": "boolean"},
    "Obesity": {"label": "Obesity", "group": "Risk factors", "unit": None, "type": "boolean"},
    "CRF": {"label": "Chronic renal failure", "group": "Risk factors", "unit": None, "type": "boolean"},
    "CVA": {"label": "Cerebrovascular accident", "group": "Risk factors", "unit": None, "type": "boolean"},
    "Airway_disease": {"label": "Airway disease", "group": "Risk factors", "unit": None, "type": "boolean"},
    "Thyroid_Disease": {"label": "Thyroid disease", "group": "Risk factors", "unit": None, "type": "boolean"},
    "CHF": {"label": "Congestive heart failure", "group": "Risk factors", "unit": None, "type": "boolean"},
    "DLP": {"label": "Dyslipidemia", "group": "Risk factors", "unit": None, "type": "boolean"},
    "BP": {"label": "Systolic BP", "group": "Vitals", "unit": "mmHg", "type": "number"},
    "PR": {"label": "Pulse rate", "group": "Vitals", "unit": "bpm", "type": "number"},
    "Edema": {"label": "Edema", "group": "Vitals", "unit": None, "type": "boolean"},
    "Weak_Peripheral_Pulse": {"label": "Weak peripheral pulse", "group": "Vitals", "unit": None, "type": "boolean"},
    "Lung_rales": {"label": "Lung rales", "group": "Symptoms", "unit": None, "type": "boolean"},
    "Systolic_Murmur": {"label": "Systolic murmur", "group": "Exam", "unit": None, "type": "boolean"},
    "Diastolic_Murmur": {"label": "Diastolic murmur", "group": "Exam", "unit": None, "type": "boolean"},
    "Typical_Chest_Pain": {"label": "Typical chest pain", "group": "Symptoms", "unit": None, "type": "boolean"},
    "Dyspnea": {"label": "Dyspnea", "group": "Symptoms", "unit": None, "type": "boolean"},
    "Function_Class": {"label": "Function class", "group": "Symptoms", "unit": None, "type": "number"},
    "Atypical": {"label": "Atypical chest pain", "group": "Symptoms", "unit": None, "type": "boolean"},
    "Nonanginal": {"label": "Nonanginal chest pain", "group": "Symptoms", "unit": None, "type": "boolean"},
    "LowTH_Ang": {"label": "Low-threshold angina", "group": "Symptoms", "unit": None, "type": "boolean"},
    "Q_Wave": {"label": "Q wave", "group": "ECG", "unit": None, "type": "boolean"},
    "St_Elevation": {"label": "ST elevation", "group": "ECG", "unit": None, "type": "boolean"},
    "St_Depression": {"label": "ST depression", "group": "ECG", "unit": None, "type": "boolean"},
    "Tinversion": {"label": "T inversion", "group": "ECG", "unit": None, "type": "boolean"},
    "LVH": {"label": "LVH", "group": "ECG", "unit": None, "type": "boolean"},
    "Poor_R_Progression": {"label": "Poor R progression", "group": "ECG", "unit": None, "type": "boolean"},
    "BBB": {"label": "Bundle branch block", "group": "ECG", "unit": None, "type": "category"},
    "FBS": {"label": "Fasting blood sugar", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "CR": {"label": "Creatinine", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "TG": {"label": "Triglycerides", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "LDL": {"label": "LDL", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "HDL": {"label": "HDL", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "BUN": {"label": "BUN", "group": "Labs", "unit": "mg/dL", "type": "number"},
    "ESR": {"label": "ESR", "group": "Labs", "unit": "mm/h", "type": "number"},
    "HB": {"label": "Hemoglobin", "group": "Labs", "unit": "g/dL", "type": "number"},
    "K": {"label": "Potassium", "group": "Labs", "unit": "mEq/L", "type": "number"},
    "Na": {"label": "Sodium", "group": "Labs", "unit": "mEq/L", "type": "number"},
    "WBC": {"label": "WBC", "group": "Labs", "unit": "/µL", "type": "number"},
    "Lymph": {"label": "Lymphocytes", "group": "Labs", "unit": "%", "type": "number"},
    "Neut": {"label": "Neutrophils", "group": "Labs", "unit": "%", "type": "number"},
    "PLT": {"label": "Platelets", "group": "Labs", "unit": "×10^3/µL", "type": "number"},
    "EF_TTE": {"label": "Ejection fraction (TTE)", "group": "Echo", "unit": "%", "type": "number"},
    "Region_RWMA": {
        "label": "Region with RWMA",
        "group": "Echo",
        "unit": None,
        "type": "number",
        "hint": "clinical hint, not anatomical evidence",
    },
    "VHD": {"label": "Valvular heart disease", "group": "Echo", "unit": None, "type": "category"},
}


def find_dataset(data_dir: Path = DATA_DIR) -> Path:
    candidates = sorted(
        [*data_dir.glob("*.xlsx"), *data_dir.glob("*.xls"), *data_dir.glob("*.csv")]
    )
    candidates = [p for p in candidates if p.name != "download_try.bin"]
    if not candidates:
        raise FileNotFoundError(
            "No dataset found in data/. Place the UCI Z-Alizadeh Sani extension xlsx there."
        )
    return candidates[0]


def load_raw(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    path = find_dataset(data_dir)
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        frame = pd.read_excel(path)
    frame.columns = [clean_column_name(col) for col in frame.columns]
    return frame


def _to_python(value):
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def encode_series(series: pd.Series) -> tuple[pd.Series, dict]:
    """Documented encoding: Y/N -> 1/0, Sex Male/Fmale -> 1/0, VHD ordinal, BBB codes."""
    name = series.name
    values = series.astype(object)
    sample = next((v for v in values if pd.notna(v)), None)

    if name == "Sex":
        mapping = {"Fmale": 0, "Female": 0, "female": 0, "Male": 1, "male": 1}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(float)
        return encoded, {"Male": 1, "Fmale": 0}

    if name == "VHD":
        mapping = {"N": 0, "n": 0, "mild": 1, "Mild": 1, "Moderate": 2, "moderate": 2, "Severe": 3, "severe": 3}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(float)
        return encoded, {"N": 0, "mild": 1, "Moderate": 2, "Severe": 3}

    if name == "BBB":
        mapping = {"N": 0, "LBBB": 1, "RBBB": 2}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(float)
        return encoded, {"N": 0, "LBBB": 1, "RBBB": 2}

    if name in {"LAD", "LCX", "RCA"}:
        mapping = {"Normal": 0, "Stenotic": 1}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(int)
        return encoded, mapping

    if name == "Cath":
        mapping = {"Normal": 0, "CAD": 1}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(int)
        return encoded, mapping

    uniq = {str(v).strip() for v in values.dropna().unique()}
    if uniq <= {"Y", "N", "y", "n"}:
        mapping = {"N": 0, "n": 0, "Y": 1, "y": 1}
        encoded = values.map(lambda v: mapping.get(str(v), 0)).astype(float)
        return encoded, {"N": 0, "Y": 1}

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().mean() > 0.95:
        return numeric.astype(float), {}

    raise ValueError(f"Unhandled encoding for column {name}: sample={sample!r} uniq={sorted(uniq)[:12]}")


def build_targets(frame: pd.DataFrame) -> pd.DataFrame:
    targets = pd.DataFrame(index=frame.index)
    lad, _ = encode_series(frame["LAD"])
    lcx, _ = encode_series(frame["LCX"])
    rca, _ = encode_series(frame["RCA"])
    cath, _ = encode_series(frame["Cath"])
    targets["cad"] = cath.astype(int)
    targets["lad"] = lad.astype(int)
    targets["lcx"] = lcx.astype(int)
    targets["rca"] = rca.astype(int)
    return targets


def add_engineered(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    hdl = out["HDL"].replace(0, np.nan)
    out["ldl_hdl_ratio"] = out["LDL"] / hdl
    out["tg_hdl_ratio"] = out["TG"] / hdl
    out["ldl_hdl_ratio"] = out["ldl_hdl_ratio"].fillna(out["ldl_hdl_ratio"].median())
    out["tg_hdl_ratio"] = out["tg_hdl_ratio"].fillna(out["tg_hdl_ratio"].median())
    return out


def build_schema(raw: pd.DataFrame, encoded: pd.DataFrame) -> list[dict]:
    schema = []
    for original, meta in FEATURE_META.items():
        if original not in encoded.columns:
            continue
        col = encoded[original]
        raw_col = raw[original]
        item = {
            "name": original,
            "label": meta["label"],
            "group": meta["group"],
            "type": meta["type"],
            "unit": meta["unit"],
            "hint": meta.get("hint"),
        }
        if meta["type"] == "number":
            item["min"] = _to_python(raw_col.min())
            item["max"] = _to_python(raw_col.max())
            item["default"] = _to_python(round(float(raw_col.median()), 2) if raw_col.dtype == float else int(raw_col.median()))
        elif meta["type"] == "boolean":
            item["allowed_values"] = [0, 1]
            item["default"] = 0
        else:
            allowed = [str(v) for v in raw_col.astype(str).unique().tolist()]
            item["allowed_values"] = allowed
            item["default"] = str(raw_col.mode().iloc[0])
        _, mapping = encode_series(raw[original])
        if mapping:
            item["encoding"] = mapping
        schema.append(item)
    for extra, label, unit in (
        ("ldl_hdl_ratio", "LDL/HDL ratio", "ratio"),
        ("tg_hdl_ratio", "TG/HDL ratio", "ratio"),
    ):
        if extra in encoded.columns:
            schema.append(
                {
                    "name": extra,
                    "label": label,
                    "group": "Labs",
                    "type": "number",
                    "unit": unit,
                    "min": _to_python(encoded[extra].min()),
                    "max": _to_python(encoded[extra].max()),
                    "default": _to_python(float(encoded[extra].median())),
                    "engineered": True,
                    "derived_from": ["LDL", "HDL"] if extra.startswith("ldl") else ["TG", "HDL"],
                }
            )
    return schema


def prepare(data_dir: Path = DATA_DIR, with_engineered: bool = True) -> dict:
    raw = load_raw(data_dir)
    assert raw.shape[0] == 303, f"Expected 303 patients, got {raw.shape[0]}"

    encoded_cols = {}
    encodings = {}
    for col in raw.columns:
        series, mapping = encode_series(raw[col])
        encoded_cols[col] = series
        encodings[col] = mapping
    encoded = pd.DataFrame(encoded_cols, index=raw.index)

    missing = encoded.isna().sum()
    if missing.any():
        for col in missing[missing > 0].index:
            encoded[col] = encoded[col].fillna(encoded[col].median())

    targets = build_targets(raw)
    feature_frame = encoded.drop(columns=[c for c in encoded.columns if c in {"LAD", "LCX", "RCA", "Cath"}])
    feature_frame = feature_frame.drop(columns=[c for c in DROP_CONSTANT if c in feature_frame.columns])
    if with_engineered:
        feature_frame = add_engineered(feature_frame)

    assert_no_leakage(feature_frame.columns)
    for col in ("LAD", "LCX", "RCA", "Cath", "CAD"):
        assert col not in feature_frame.columns, col

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_schema(raw, feature_frame)
    payload = {
        "n_rows": int(len(feature_frame)),
        "n_features": int(feature_frame.shape[1]),
        "leakage_columns": list(LEAKAGE_COLUMNS),
        "dropped_constant": sorted(DROP_CONSTANT),
        "encodings": {k: v for k, v in encodings.items() if v},
        "features": schema,
        "feature_names": list(feature_frame.columns),
    }
    (MODELS_DIR / "feature_schema.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "raw": raw,
        "X": feature_frame,
        "y": targets,
        "schema": payload,
        "encodings": encodings,
    }


def vectorize_patient(patient: dict, schema_payload: dict) -> pd.DataFrame:
    """Map a UI/API dict onto the training feature order."""
    assert_no_leakage(patient.keys())
    names = schema_payload["feature_names"]
    by_name = {item["name"]: item for item in schema_payload["features"]}
    encodings = schema_payload.get("encodings", {})
    accepted_names = {name for name in names if not by_name[name].get("engineered")}
    unknown = set(patient) - accepted_names
    if unknown:
        raise ValueError(f"Unknown patient feature(s): {sorted(unknown)}")
    row = {}
    for name in names:
        if name in {"ldl_hdl_ratio", "tg_hdl_ratio"}:
            continue
        meta = by_name[name]
        raw_value = patient.get(name, meta.get("default"))
        mapping = encodings.get(name) or meta.get("encoding") or {}
        try:
            mapped = mapping.get(raw_value, mapping.get(str(raw_value)))
        except TypeError:
            mapped = None
        if mapped is not None:
            row[name] = float(mapped)
        elif isinstance(raw_value, bool):
            row[name] = float(raw_value)
        else:
            try:
                row[name] = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid value for feature {name}: {raw_value!r}") from exc
        if meta.get("type") == "category":
            allowed = meta.get("allowed_values", [])
            if raw_value not in allowed and str(raw_value) not in allowed:
                raise ValueError(f"Invalid value for {name}; allowed values: {allowed}")
        if meta.get("type") in {"number", "boolean"}:
            lower = meta.get("min")
            upper = meta.get("max")
            if meta.get("type") == "boolean" and row[name] not in {0.0, 1.0}:
                raise ValueError(f"{name} must be 0 or 1")
            if lower is not None and row[name] < float(lower):
                raise ValueError(f"{name} must be at least {lower}")
            if upper is not None and row[name] > float(upper):
                raise ValueError(f"{name} must be at most {upper}")
    frame = pd.DataFrame([row])
    if "ldl_hdl_ratio" in names or "tg_hdl_ratio" in names:
        frame = add_engineered(frame)
    frame = frame[names]
    assert_no_leakage(frame.columns)
    return frame


def main() -> None:
    bundle = prepare()
    print(f"Prepared X={bundle['X'].shape} y={bundle['y'].shape}")
    print("Features:", list(bundle["X"].columns))
    print("Wrote models/feature_schema.json")
    print("Target rates:")
    print(bundle["y"].mean().to_string())


if __name__ == "__main__":
    main()
