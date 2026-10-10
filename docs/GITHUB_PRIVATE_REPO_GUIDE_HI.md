# GitHub Private Repo Setup Guide

Ye guide `Hriday.Ai` project ko private GitHub repository me push karne ke liye
hai.

## 1. GitHub par private repo banao

1. GitHub dashboard khol.
2. Top right `+` button par click kar.
3. `New repository` select kar.
4. Repository name: `Hriday.Ai`
5. Owner: `sundram-yadav`
6. Visibility: `Private`
7. `Add a README file` unchecked rakhna, kyunki local README already hai.
8. `Create repository` click kar.

## 2. Local project ko git repo banao

PowerShell me project folder ke andar:

```powershell
cd "C:\Users\sundr\OneDrive\Desktop\Hriday.Ai"
git init
git branch -M main
git add .
git commit -m "Initial Hriday.Ai project setup"
```

## 3. GitHub remote add karo

GitHub repo page par jo HTTPS URL milega, usse remote add karo:

```powershell
git remote add origin https://github.com/sundram-yadav/Hriday.Ai.git
git push -u origin main
```

Push ke time browser login ya token mang sakta hai. GitHub Desktop installed ho
to usse bhi authenticate ho sakta hai.

## 4. Important

- `data/` folder commit nahi hoga. Dataset local rakho.
- `models/` generated artifacts commit nahi honge jab tak final submission ke
  liye explicitly decide na karo.
- Secrets `.env` me rakho; `.env` GitHub par push mat karo.

## 5. Project banane ka A to Z flow

1. Dataset ko `data/` me rakho.
2. ML pipeline banao: explore, preprocess, train, metrics, SHAP.
3. Backend banao: FastAPI endpoints `/schema`, `/predict`, `/explain`,
   `/counterfactual`.
4. Frontend banao: React dashboard, form, 3D heart, artery risk mapping.
5. Tests chalao: leakage test, schema test, predict smoke test, API test.
6. Docs finalize karo: README, report, demo script, attributions.
7. Demo video record karo.
8. Deploy backend/frontend.
9. Submission ke liye public/private visibility requirement check karo.
