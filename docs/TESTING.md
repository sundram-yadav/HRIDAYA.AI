# Testing Checklist

## Automated checks

```powershell
pytest
cd frontend
npm run build
```

Current result:

- Python tests: passing
- Frontend build: passing

## Manual UI checks

- Start backend at `http://127.0.0.1:8000`.
- Start frontend at `http://127.0.0.1:5173`.
- Load the page and confirm the disclaimer is visible.
- Load each sample patient.
- Move numeric sliders and confirm probabilities update.
- Toggle boolean fields and confirm probabilities update.
- Click LAD, LCX, and RCA labels/cards.
- Confirm the explanation panel changes for the selected target.
- Click "Suggest changes" and confirm the what-if panel appears.
- Narrow the browser window and confirm the layout stacks cleanly.

## API checks

- `GET /health`
- `GET /schema`
- `GET /metrics`
- `GET /sample-patients`
- `POST /predict`
- `POST /explain`
- `POST /counterfactual`

## Leakage check

Send a patient payload containing `LAD`, `LCX`, `RCA`, `CAD`, or `Cath`. The
backend model layer should reject it instead of silently using it.
