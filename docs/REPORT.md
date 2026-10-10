# Hriday.Ai Report Draft

## Problem and approach

Coronary artery disease risk is usually discussed through tables, reports, and
separate diagnostic findings. Hriday.Ai turns structured clinical inputs into a
single dashboard that estimates overall CAD risk and vessel-level risk for LAD,
LCX, and RCA. The goal is to make the result easier to inspect, explain, and
present during a hackathon demo.

## Current implementation

The current repository contains a working dashboard build:

- FastAPI backend with schema, prediction, explanation, sample-patient, metrics,
  and counterfactual endpoints.
- React frontend with a dynamic input form, vessel risk cards, explanation
  panel, metrics table, and heart/vessel visualization.
- Leakage checks that reject label-like columns from model input.
- Tests covering API health, prediction smoke flow, and leakage rejection.

## Dataset and leakage prevention

The final model is intended to use the Z-Alizadeh Sani extension dataset. The
dataset file is not committed to this repository. It should be placed locally in
`data/`.

The main leakage risk is accidentally using labels such as `Cath`, `CAD`, `LAD`,
`LCX`, or `RCA` as features. The repository keeps a `LEAKAGE_COLUMNS` list and
has tests to reject these fields. Final training must also assert that these
columns are excluded from every target-specific feature matrix.

## Model status

The present API uses the included risk engine. Dataset-trained models can be
plugged into the same API contract after the local training workflow is
completed.

Final metrics must not be written by hand. They should come from a real training
run saved into `models/metrics.json`.

## Visualization

The frontend uses a lightweight heart and vessel map. LAD, LCX, and RCA are
shown separately. Higher probability changes the vessel color and narrows the
rendered line, giving both color and shape cues. The visualization is designed
to be stable on a normal laptop browser.

## Interpretability and uncertainty

The explanation panel shows transparent risk-engine components. In the trained
version, this should be replaced by SHAP values for each target. Each
prediction includes a confidence interval-style range so the interface can show
uncertainty instead of only a single number.

## Limitations

- Current scores are produced by the included risk engine, not externally
  validated clinical predictions.
- Dataset training is still pending.
- No external validation is available yet.
- RWMA is treated only as a clinical hint, not anatomical lesion evidence.
- The system is for education and decision-support demonstration only.

## Usage

Run the backend:

```powershell
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.
