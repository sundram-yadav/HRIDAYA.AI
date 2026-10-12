# HRIDAYA.AI — Progress

Hackathon: Multimodal AI Hackathon 2026, Track A.
Workspace: `HRIDAYA.AI` (existing git repo). Dataset inspected from UCI id=411 xlsx.

Assumptions recorded in CHANGELOG.md.

| Phase | Status | Notes |
| --- | --- | --- |
| 0. Bootstrap and inspect data | done | 303 rows × 59 columns, no missing raw cells. Targets and counts recorded above; dataset is local only. |
| 1. Leakage-safe ML pipeline | done | Seed-42 training completed; all four model bundles, registry, metrics, synthetic demo samples, and 17 plots generated. See `models/metrics.json`. |
| 2. FastAPI backend | done | All routes exercised with saved artifacts. Schema response annotation fixed; mixed-case leakage, unknown feature, and invalid range checks are tested. |
| 3. 3D viewer | done | Procedural fallback and config-driven vessels in place; selected target now synchronizes camera focus. No external GLB is included. |
| 4. Clinical dashboard | done | Frontend import mismatch fixed; localized labels, SHAP/metrics/what-if surfaces and responsive layout are present. Production build and dependency audit pass. |
| 5. Visual polish and guided demo | done | Guided sample flow, focus sequence, heartbeat, color/shape cues, theme/language controls and baseline per-target risk deltas implemented and browser-checked. |
| 6. Integration and QA | done | Python tests pass (16); frontend build and npm audit pass; browser flows and 320px/390px responsive layouts verified without horizontal overflow. Render host/CORS configuration and artifact compression were checked. |
| 7. Deployment files | prepared | Render Blueprint creates API/static services; compressed model registry, production API host handling, and health/CORS configuration are in place. Render account setup and live production smoke test remain. |
| 8. Documentation and submission pack | done (code/docs) | README/results, report, attributions, demo script, checklist, and test notes updated. Screenshot capture, PDF generation/page count, public video/repo/demo links, project license and submission remain owner actions. |
