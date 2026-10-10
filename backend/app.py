from __future__ import annotations

from typing import Any, Dict, List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.prototype_model import (
    FEATURE_SCHEMA,
    METRICS,
    SAMPLE_PATIENTS,
    explain_patient,
    predict_all,
    suggest_counterfactual,
)


app = FastAPI(
    title="Hriday.Ai API",
    description="Prototype API for cardiovascular risk visualization and explanation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TargetName = Literal["cad", "lad", "lcx", "rca"]


class PatientRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    target: TargetName = "cad"


class CounterfactualRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    target: TargetName = "cad"


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "mode": "prototype"}


@app.get("/schema")
def schema() -> Dict[str, List[Dict[str, Any]]]:
    return {"features": FEATURE_SCHEMA}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return METRICS


@app.get("/sample-patients")
def sample_patients() -> Dict[str, Any]:
    return {"patients": SAMPLE_PATIENTS}


@app.post("/predict")
def predict(request: PatientRequest) -> Dict[str, Any]:
    try:
        return predict_all(request.patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/explain")
def explain(request: ExplainRequest) -> Dict[str, Any]:
    try:
        return explain_patient(request.patient, request.target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/counterfactual")
def counterfactual(request: CounterfactualRequest) -> Dict[str, Any]:
    try:
        return suggest_counterfactual(request.patient, request.target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
