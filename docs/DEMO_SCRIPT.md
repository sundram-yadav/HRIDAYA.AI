# Six-minute demo script

## 0:00–0:35 — Introduce the project

“HRIDAYA.AI is an educational cardiovascular-risk visualization prototype. It
estimates angiographic CAD and LAD, LCX, and RCA labels from structured clinical
features. These internal validation estimates are not diagnoses.”

Show the permanent disclaimer banner and mention the 303-patient,
single-centre-data limitation.

## 0:35–1:20 — Show the dashboard

Point out the procedural 3D heart, separate risk cards, schema-driven patient
form, and the live prediction flow. Explain that `Cath`, `LAD`, `LCX`, and `RCA`
are labels excluded from every model input.

## 1:20–2:10 — Load a real sample

Choose the higher-risk sample from the dropdown. Show the four probabilities,
their model-spread ranges, and the confidence warning if displayed. State that
these are cross-validated models trained on a small dataset, not clinical
probabilities.

## 2:10–3:05 — Explore anatomy and explanations

Rotate and zoom the heart, click LAD, LCX, and RCA, and show the color/shape cue
and camera focus. Open a vessel explanation and read one positive and one
negative SHAP contribution. Clarify that SHAP describes model behavior, not
causal effects. If RWMA is present, point out its “clinical hint, not anatomical
evidence” label.

## 3:05–4:10 — Illustrative what-if

Enter what-if mode and change one or two inputs. Show the percentage-point
change from the remembered baseline. Run “Suggest changes” and read the
illustrative-only warning. Do not present the suggested values as medical
advice.

## 4:10–5:10 — Validation metrics

Open the metrics tab. Point out ROC-AUC, F1, and recall mean ± standard
deviation from repeated stratified five-fold CV. Note that LCX/RCA scores are
modest, calibration did not help RCA Brier score, and no external validation
has been done.

## 5:10–6:00 — Close with limitations

“This prototype helps visualize model outputs and their feature contributions.
It has only 303 single-centre records, no external validation, and is not for
clinical use.” End by showing the disclaimer/footer.

## Recording checklist

- Use a 3–10 minute recording, preferably around six minutes.
- Close private tabs and hide local credentials/notifications.
- Use the local `.\run_all.bat` app or the final verified public demo.
- Test microphone and screen share first; OBS or Loom are suitable.
- Re-check the uploaded video permissions and paste its URL into the submission checklist.
