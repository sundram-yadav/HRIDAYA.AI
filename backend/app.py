from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ml.leakage import LEAKAGE_COLUMNS
from ml.predict import (
    DISCLAIMER,
    explain_patient,
    load_artifacts,
    predict_all,
    suggest_counterfactual,
)

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figures"


def _normalize_origin(origin: str) -> str:
    normalized = origin.strip().rstrip("/")
    if normalized and not normalized.startswith(("http://", "https://")):
        return f"https://{normalized}"
    return normalized


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global ART
    try:
        ART = load_artifacts()
    except FileNotFoundError:
        ART = None
    yield


app = FastAPI(
    title="HRIDAYA.AI API",
    description="CAD and vessel-stenosis prediction with SHAP explanations.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
extra_origins = os.environ.get("ALLOWED_ORIGINS") or os.environ.get("ALLOWED_ORIGIN") or os.environ.get("FRONTEND_ORIGIN", "")
for configured_origin in extra_origins.split(","):
    origin = _normalize_origin(configured_origin)
    if origin:
        if origin not in origins:
            origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ART: dict | None = None
TargetName = Literal["cad", "lad", "lcx", "rca"]


class PatientRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    target: TargetName = "cad"


class CounterfactualRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    target: TargetName = "cad"


def artifacts() -> dict:
    global ART
    if ART is None:
        try:
            ART = load_artifacts()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ART


@app.get("/health")
def health() -> Dict[str, Any]:
    artifacts()
    return {"status": "ok", "mode": "trained", "disclaimer": DISCLAIMER}


@app.get("/schema")
def schema() -> Dict[str, Any]:
    data = artifacts()
    features = [f for f in data["schema"]["features"] if not f.get("engineered")]
    return {"features": features, "leakage_columns": list(LEAKAGE_COLUMNS)}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return artifacts()["metrics"]


@app.get("/sample-patients")
def sample_patients() -> Dict[str, Any]:
    return {"patients": artifacts()["samples"]}


def _reject_leakage(patient: Dict[str, Any]) -> None:
    leakage_by_lower = {name.lower() for name in LEAKAGE_COLUMNS}
    forbidden = {name for name in patient if name.lower() in leakage_by_lower}
    if forbidden:
        raise HTTPException(
            status_code=400,
            detail=f"Input contains leakage columns: {sorted(forbidden)}",
        )


@app.post("/predict")
def predict(request: PatientRequest) -> Dict[str, Any]:
    _reject_leakage(request.patient)
    try:
        return predict_all(request.patient, artifacts())
    except (ValueError, AssertionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/explain")
def explain(request: ExplainRequest) -> Dict[str, Any]:
    _reject_leakage(request.patient)
    try:
        return explain_patient(request.patient, request.target, artifacts())
    except (ValueError, AssertionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/counterfactual")
def counterfactual(request: CounterfactualRequest) -> Dict[str, Any]:
    _reject_leakage(request.patient)
    try:
        return suggest_counterfactual(request.patient, request.target, artifacts())
    except (ValueError, AssertionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/figures/{name}")
def figures(name: str):
    safe = Path(name).name
    path = FIGURES / safe
    if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".svg"}:
        raise HTTPException(status_code=404, detail="Figure not found")
    return FileResponse(path)
