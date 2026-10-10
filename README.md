# Hriday.Ai

Multimodal cardiovascular risk visualization and prediction project for Track A:
Cardiovascular Risk Visualization & Prediction.

This repository is intended to predict overall CAD status and LAD, LCX, RCA
stenosis risk from clinical inputs, visualize vessel-level risk on an
interactive 3D heart, and explain predictions using SHAP.

## Current Status

Project setup is being prepared from the Track A Claude prompt pack. The final
ML pipeline requires the Z-Alizadeh Sani extension dataset to be placed in
`data/`.

## Planned Stack

- ML: Python, pandas, scikit-learn, XGBoost, SHAP
- Backend: FastAPI, pydantic, joblib
- Frontend: React, Vite, Three.js, @react-three/fiber, Recharts
- Testing: pytest, frontend build checks

## Repository Structure

```text
data/       Dataset files, not committed
ml/         Data exploration, preprocessing, training, prediction code
models/     Trained model artifacts and generated schema/metrics
backend/    FastAPI service
frontend/   React + Vite dashboard and 3D viewer
docs/       Report, testing notes, demo script, generated figures
tests/      Python tests
```

## Medical Disclaimer

For decision support / educational purposes only. Not a substitute for formal
diagnostic imaging.

## Next Steps

1. Add the dataset file to `data/`.
2. Build the ML pipeline with leakage prevention.
3. Add the FastAPI prediction service.
4. Add the React 3D dashboard.
5. Generate metrics, figures, report, demo script, and submission checklist.
