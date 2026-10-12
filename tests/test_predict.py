from pathlib import Path

import pytest

from ml.leakage import assert_no_leakage
from ml.predict import explain_patient, predict_all

REGISTRY = Path("models/registry.joblib")


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_predict_smoke_and_no_leakage_in_schema_file():
    import json

    schema = json.loads(Path("models/feature_schema.json").read_text(encoding="utf-8"))
    assert_no_leakage(schema["feature_names"])
    patient = {item["name"]: item["default"] for item in schema["features"] if not item.get("engineered")}
    out = predict_all(patient)
    assert set(out["targets"]) == {"cad", "lad", "lcx", "rca"}
    for row in out["targets"].values():
        assert 0.0 <= row["probability"] <= 1.0
        assert row["ci_low"] <= row["probability"] <= row["ci_high"]
        assert 0.0 <= row["ci_low"] <= row["ci_high"] <= 1.0


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_explain_returns_top_features():
    import json

    schema = json.loads(Path("models/feature_schema.json").read_text(encoding="utf-8"))
    patient = {item["name"]: item["default"] for item in schema["features"] if not item.get("engineered")}
    exp = explain_patient(patient, "lad")
    assert len(exp["contributions"]) <= 8
    assert exp["contributions"]
