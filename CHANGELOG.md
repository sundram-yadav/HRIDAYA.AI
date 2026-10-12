# Changelog

## 2026-10-12

- Rebuilt Track A toward a full trained pipeline + 3D dashboard (replacing the heuristic demo).
- Assumption: workspace git repo is `HRIDAYA.AI` (already initialized); we did not re-run `git init`.
- Assumption: overall CAD target is `Cath` (`CAD` vs `Normal`). The xlsx has no separate `CAD` column.
- Assumption: `BP` is systolic blood pressure (mmHg). Diastolic BP is not in the dataset, so pulse pressure was not engineered.
- Assumption: `Length` is height in cm. `Exertional CP` is constant (`N`) and is dropped as uninformative, not as leakage.
- Assumption: `Region RWMA` is an input echo feature (0–4), never a lesion map.
- Dataset file saved locally as `data/z_alizadeh_sani_extension.xlsx` (UCI id=411, 303×59, 0 missing).
- Python 3.14 is the only interpreter on this machine; package pins follow what installs in `.venv`.
- Trained and saved all four target models, registry, real repeated-CV metrics, sample patients, and validation figures using seed 42.
- Replaced dataset-derived browser examples with synthetic patient profiles before deployment; compressed the runtime model registry for GitHub compatibility.
- Fixed the frontend API/localization export mismatch, baseline risk-delta display, camera focus synchronization, backend schema response typing, and explicit invalid-input rejection.
- Updated the stale README/report/testing/demo documents; added dataset/software attributions and a submission checklist. Deployment files intentionally remain out of scope.
- Regenerated the frontend npm lockfile to match its pinned manifest. Upgraded Vite and Drei to patched versions after npm audit findings; both remain exactly pinned.
- Validation environment: portable Node.js 24.20.0 was downloaded to the temporary directory and checksum-verified; it is not a system install. The final test/build/audit results are recorded in `docs/TESTING.md`.
