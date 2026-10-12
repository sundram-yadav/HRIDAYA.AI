# Testing and QA

## Automated verification (2026-10-12)

| Check | Result | Evidence |
| --- | --- | --- |
| ML preprocessing, target/leakage tests, schema/input checks | Pass | `python -m pytest -q` |
| Trained prediction, SHAP explanation, counterfactual and API smoke tests | Pass | 16 passed; all saved model targets present |
| API rejects mixed-case leakage, unknown names and out-of-range values | Pass | `tests/test_backend.py` |
| Sample patient API serves synthetic profiles only | Pass | `tests/test_backend.py`; no dataset row indices or actual rows in `models/sample_patients.json` |
| Model metrics and validation figures generated | Pass | `models/metrics.json`; 17 figure files |
| Frontend production compilation | Pass | `npm run build` with Node 24.20.0; 1,230 modules transformed |
| Frontend dependency audit | Pass | `npm audit`; 0 vulnerabilities |
| Local browser interaction and narrow-screen review | Pass for listed flows | Sample predictions, SHAP, metrics/figures, what-if deltas, guided demo, 3D render, and 320px/390px layouts checked |
| Clean-machine setup (fresh venv + npm ci) | Partial | npm lockfile aligned; Python clean reinstall not repeated |

Last full test run: **16 passed**. One existing Starlette/httpx deprecation
warning remains.

## Run the automated checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm ci
npm run build
npm audit
```

## API coverage

Automated tests exercise:

- `GET /health`, `/schema`, `/metrics`, `/sample-patients`, and `/figures/model_comparison.png`
- `POST /predict` for all four targets, including CI bounds
- `POST /explain` for SHAP contributions
- `POST /counterfactual` for the illustrative-only disclaimer
- Leakage (including mixed-case aliases), unknown feature, and range rejection

The local QA run returned 200 for API read/prediction/explanation/what-if/figure
routes and 400 for rejected input cases. In the browser, sample loading updated
predictions, SHAP displayed eight contributions, all four metrics and their
figures loaded, what-if deltas changed after edits, and the guided demo reached
completion. The 3D heart rendered without console errors or failed requests.
At 320px and 390px viewports, document scroll width matched the available client
width (305px and 375px respectively), with no horizontal page overflow.

## Manual browser checklist

- [x] Open the local dashboard and load a sample patient; confirm predictions update.
- [x] Confirm SHAP contributions, all four metrics/figures, and edited what-if deltas render.
- [x] Run the guided demo through completion and confirm the 3D heart renders.
- [x] Inspect the browser console/network and verify 320px and 390px viewports have no horizontal page overflow.
- [ ] Confirm the exact disclaimer appears in the sticky header area and footer.
- [ ] Load low, intermediate, and higher-risk examples; check cards and heart update.
- [ ] Change a numeric slider, categorical value, and boolean; confirm debounced predictions update.
- [ ] Select each artery on both its card and the 3D vessel; confirm camera focus and SHAP panel change.
- [ ] Rotate, zoom, pan, pulse-toggle, and reset the camera.
- [ ] Run “Suggest changes”; confirm baseline/after values and the medical-advice warning.

Do not mark manual/browser steps as passing without actually completing them.
