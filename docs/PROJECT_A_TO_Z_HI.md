# Hriday.Ai A to Z Explanation

## Project ka simple idea

Hriday.Ai ek cardiovascular risk visualization app hai. User patient ke clinical
features enter karega, model CAD aur coronary arteries LAD, LCX, RCA ke risk
predict karega, aur frontend 3D heart par risk ko color/thickness se show karega.

## Track A judging ke hisab se parts

1. Predictive performance: real dataset par validation, repeated CV,
   ROC-AUC, F1, recall, calibration.
2. 3D visualization: heart + LAD/LCX/RCA arteries, risk-based color and narrowing.
3. Interpretability: SHAP top features, plain-language explanation.
4. Integration: ML model + FastAPI + React frontend live connected.
5. Technical quality: clean repo, tests, docs, run commands.

## Leakage ka sabse important rule

LAD, LCX, RCA, Cath jaise columns target labels hain. Inko model input feature
ke roop me kabhi use nahi karna. Agar ye input me chale gaye to model incorrect high
accuracy dikhayega. Isliye code me `LEAKAGE_COLUMNS` constant aur tests hone
chahiye.

## Backend endpoints

- `GET /health`: server live hai ya nahi.
- `GET /schema`: frontend form ke features.
- `GET /metrics`: saved model metrics.
- `GET /sample-patients`: demo patients.
- `POST /predict`: CAD/LAD/LCX/RCA probabilities.
- `POST /explain`: SHAP explanation.
- `POST /counterfactual`: illustrative what-if suggestions.

## Frontend experience

Left side 3D heart rahega. Right side input form, CAD card, vessel cards,
SHAP detail, metrics tab, aur what-if mode rahega. Top aur footer me medical
disclaimer visible rahega.

## Abhi kya pending hai

- Dataset file `data/` me add karna.
- ML code likhna aur train karna.
- Backend implementation.
- Frontend implementation.
- Tests, screenshots, report, video, deploy.
