from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import _normalize_origin, app

client = TestClient(app)
REGISTRY = Path("models/registry.joblib")


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "mode": "trained",
        "disclaimer": "For decision support / educational purposes only. Not a substitute for formal diagnostic imaging.",
    }


def test_render_origins_are_normalized() -> None:
    assert _normalize_origin(" hridaya-ai-web.onrender.com/ ") == "https://hridaya-ai-web.onrender.com"
    assert _normalize_origin("https://example.test/") == "https://example.test"
    assert _normalize_origin("") == ""


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_schema_and_metrics() -> None:
    schema = client.get("/schema")
    assert schema.status_code == 200
    assert schema.json()["features"]
    assert schema.json()["leakage_columns"]
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert set(body["targets"]) == {"cad", "lad", "lcx", "rca"}
    assert body["targets"]["cad"]["roc_auc"]["mean"] > 0.5


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_predict_smoke() -> None:
    response = client.post("/predict", json={"patient": {"Age": 60, "Sex": "Male"}})
    assert response.status_code == 200
    body = response.json()
    assert set(body["targets"].keys()) == {"cad", "lad", "lcx", "rca"}
    assert 0 <= body["targets"]["cad"]["probability"] <= 1


def test_leakage_columns_rejected() -> None:
    response = client.post("/predict", json={"patient": {"LAD": 1, "Age": 60}})
    assert response.status_code == 400
    assert "leakage" in response.json()["detail"].lower()


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_invalid_patient_inputs_are_rejected() -> None:
    unknown = client.post("/predict", json={"patient": {"Age": 60, "made_up_feature": 1}})
    assert unknown.status_code == 400
    assert "unknown" in unknown.json()["detail"].lower()

    schema = client.get("/schema").json()
    age = next(feature for feature in schema["features"] if feature["name"] == "Age")
    outside_range = client.post(
        "/predict",
        json={"patient": {"Age": age["max"] + 1}},
    )
    assert outside_range.status_code == 400
    assert "Age must be at most" in outside_range.json()["detail"]

    mixed_case_leakage = client.post("/predict", json={"patient": {"lAd": 1}})
    assert mixed_case_leakage.status_code == 400
    assert "leakage" in mixed_case_leakage.json()["detail"].lower()


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_explain_and_counterfactual() -> None:
    explain = client.post("/explain", json={"patient": {"Age": 62, "Sex": "Male"}, "target": "cad"})
    assert explain.status_code == 200
    assert explain.json()["contributions"]
    cf = client.post("/counterfactual", json={"patient": {"Age": 68, "BP": 170, "LDL": 180}, "target": "cad"})
    assert cf.status_code == 200
    assert "Illustrative" in cf.json()["disclaimer"]


@pytest.mark.skipif(not REGISTRY.exists(), reason="Train models first")
def test_sample_patients_and_figures() -> None:
    samples = client.get("/sample-patients")
    assert samples.status_code == 200
    assert samples.json()["patients"]
    assert all("synthetic" in patient["label"].lower() for patient in samples.json()["patients"])
    assert all("row_index" not in patient for patient in samples.json()["patients"])
    fig = client.get("/figures/model_comparison.png")
    assert fig.status_code == 200
