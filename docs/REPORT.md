# HRIDAYA.AI: Cardiovascular Risk Visualization

## Problem and approach

Coronary artery disease (CAD) and vessel stenosis are commonly reviewed through
clinical tables and angiography findings. HRIDAYA.AI is an educational
prototype that accepts structured clinical features, estimates angiographic
CAD and LAD, LCX, and RCA labels, and visualizes vessel estimates on an
interactive low-poly heart. It is not a diagnostic system.

## Dataset and leakage prevention

The UCI extension of the Z-Alizadeh Sani dataset contains 303 patients and 59
columns. The target labels are `Cath` (overall CAD) and `LAD`, `LCX`, and `RCA`
(stenotic/normal). All four target columns are excluded from the feature matrix
for every target; case-normalized runtime checks reject them from API requests.
The preprocessing pipeline asserts this invariant, and dedicated unit/API
tests exercise both direct and HTTP rejection. Dataset inspection and observed
class counts are documented in `data_summary.md`.

The preprocessor maps observed categories explicitly, drops the constant
`Exertional_CP` field, imputes any numeric missing values with training-data
medians, and derives LDL/HDL and TG/HDL ratios. Seed 42 is used throughout.
The raw file remains local and is not included in source control.

## Model and validation methodology

For each target, logistic regression, random forest, and XGBoost were compared.
The reported model-selection comparison uses repeated stratified five-fold CV
(five repeats); candidate hyperparameters are selected in an inner three-fold
search restricted to each outer training fold. The best nested-CV ROC-AUC model
is compared with a soft-voting model. Feature selection and random oversampling
are evaluated inside folds as ablations; the winning configuration is
re-evaluated with repeated five-fold CV. No label column is used as a feature.
A classifier-chain ablation predicts earlier vessel labels at inference time
and reports those results separately; ground-truth vessel labels are not
inference inputs.

Sigmoid and isotonic calibration are compared using cross-validated Brier
scores. The selected final classifiers are fitted to the available dataset and
saved to `models/`; plots and all displayed validation numbers come from
`models/metrics.json` and `docs/figures/`.

## Results

Mean ± standard deviation from the saved repeated five-fold results:

| Target | Selected model | ROC-AUC | Accuracy | Precision | Recall | F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| CAD | Soft voting | 0.923 ± 0.034 | 0.859 ± 0.045 | 0.925 ± 0.037 | 0.874 ± 0.054 | 0.898 ± 0.034 |
| LAD | Random forest | 0.850 ± 0.046 | 0.784 ± 0.036 | 0.812 ± 0.050 | 0.826 ± 0.057 | 0.817 ± 0.030 |
| LCX | Random forest | 0.729 ± 0.057 | 0.683 ± 0.044 | 0.596 ± 0.067 | 0.620 ± 0.073 | 0.605 ± 0.056 |
| RCA | Soft voting | 0.727 ± 0.059 | 0.673 ± 0.057 | 0.564 ± 0.085 | 0.598 ± 0.126 | 0.575 ± 0.088 |

Scores are internal cross-validation estimates on a small dataset. The saved
classifier-chain ablation increased mean vessel ROC-AUC by 0.021 (LAD), 0.024
(LCX), and 0.046 (RCA) in its separate two-repeat comparison; it is not the
deployed model. Sigmoid calibration reduced Brier score for CAD (0.105 to
0.093), LAD (0.171 to 0.154), and LCX (0.211 to 0.207), but did not improve
RCA (0.203 to 0.205). These results do not establish clinical utility.

## 3D pipeline and dashboard

The React dashboard obtains input metadata from the FastAPI schema endpoint.
Three.js renders a procedural heart (used when no credited GLB is supplied)
and configurable Catmull–Rom paths for LAD, LCX, and RCA. Predicted vessel
probability changes color and a local tube-radius cue; labels and percentage
text supplement color. Orbit controls, vessel selection, camera focus,
heartbeat, responsive input controls, and validation charts are provided.
Device pixel ratio is capped at 1.5 and there is no post-processing.

## Interpretability and uncertainty

Patient explanations use permutation SHAP and return up to eight ranked
feature contributions with direction. The visualized arteries encode model
probabilities, not observed anatomy. `Region_RWMA` is only an echo input and is
explicitly labelled a “clinical hint, not anatomical evidence.”

Displayed ranges are the 2.5th and 97.5th percentiles across eight
bootstrap-refitted models. They represent model-to-model prediction spread,
not calibrated patient-level confidence intervals or clinical uncertainty.
What-if suggestions greedily change selected input variables and are
illustrative, not causal or medical advice.

## Limitations, ethics, and usage

There are only 303 single-centre records, no external validation, no
prospective evaluation, and no evidence that the estimates improve outcomes.
LCX/RCA scores are modest. Selection/tuning on a small cohort can still yield
optimistic estimates; external validation is required. The interface is for
educational demonstration only, not diagnosis, triage, treatment, or clinical
use. It permanently displays: “For decision support / educational purposes
only. Not a substitute for formal diagnostic imaging.”

From the project root, install pinned requirements and start the local
development app with `.\run_all.bat` (Windows) or `./run_all.sh` (Unix-like
systems). Retrain the pipeline with `python -m ml.run_all`. Node.js 20.19+ and
the local UCI dataset are prerequisites. API routes, exact commands, and test
results are in `README.md` and `TESTING.md`.

To export this Markdown report to PDF from the project root, install Pandoc and
a LaTeX engine, then run:

```powershell
pandoc docs/REPORT.md -o docs/REPORT.pdf --pdf-engine=xelatex
pdfinfo docs/REPORT.pdf
```

Check the `Pages` field from `pdfinfo`; keep it at six pages or fewer by
adjusting print margins/font size before submission. The PDF itself has not yet
been generated or page-count verified.
