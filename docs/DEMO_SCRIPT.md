# Demo Script

Target length: 5 to 7 minutes.

## 0:00 - 0:30 Opening

Introduce Hriday.Ai as a cardiovascular risk visualization dashboard. Mention
that it estimates overall CAD plus LAD, LCX, and RCA risk from structured
clinical inputs.

## 0:30 - 1:15 Disclaimer and layout

Point to the disclaimer at the top. Explain that this is not a diagnostic tool.
Show the main layout: heart visualization on the left, risk cards and
explanation panel on the right, patient inputs below.

## 1:15 - 2:15 Sample patient

Load the higher risk sample patient. Show how the CAD and vessel probabilities
change. Click LAD, LCX, and RCA one by one and explain that each vessel has its
own focused panel.

## 2:15 - 3:15 Explanations

Open one vessel detail and walk through the explanation bars. Say clearly that
the current build uses transparent explanation components and the trained
model path can replace these with SHAP values.

## 3:15 - 4:15 What-if mode

Click "Suggest changes." Explain that the suggestions are illustrative only and
not medical advice. Show the before and after risk estimate.

## 4:15 - 5:15 Technical architecture

Briefly describe the architecture: React frontend, FastAPI backend, schema-driven
form, leakage checks, and future training pipeline.

## 5:15 - 6:00 Limitations

Explain the current scope: local dataset training and external validation are
the next stages, and final metrics should come from a saved training run.

## 6:00 - 6:30 Close

Summarize the value: one place to enter clinical features, inspect vessel risk,
see uncertainty, and understand the factors behind the estimate.
