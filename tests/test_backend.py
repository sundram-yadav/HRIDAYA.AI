from fastapi.testclient import TestClient

from backend.app import app
from backend.risk_engine import normalize_patient


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_smoke() -> None:
    response = client.post("/predict", json={"patient": {"age": 60, "sex": "male"}})
    assert response.status_code == 200
    body = response.json()
    assert set(body["targets"].keys()) == {"cad", "lad", "lcx", "rca"}
    assert 0 <= body["targets"]["cad"]["probability"] <= 1


def test_leakage_columns_rejected() -> None:
    try:
        normalize_patient({"LAD": 1, "age": 60})
    except ValueError as exc:
        assert "leakage" in str(exc).lower()
    else:
        raise AssertionError("Leakage column was accepted")


def test_api_rejects_leakage_columns() -> None:
    response = client.post("/predict", json={"patient": {"LAD": 1, "age": 60}})
    assert response.status_code == 400
    assert "leakage" in response.json()["detail"].lower()
