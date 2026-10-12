# Deploy HRIDAYA.AI on Render

The repository includes a Render Blueprint (`render.yaml`) that creates a
FastAPI web service and a Vite static site. The frontend receives the API host
from Render at build time. There are no API keys and no production `.env` file
is needed.

## Before you deploy

1. Push the reviewed code to the GitHub `main` branch.
2. Confirm the repository contains `models/registry.joblib`,
   `models/feature_schema.json`, `models/metrics.json`,
   `models/sample_patients.json`, and the PNGs in `docs/figures/`.
3. Keep `data/z_alizadeh_sani_extension.xlsx` private and out of Git. Render
   serves the saved models; it does not retrain them during deployment.

## Create the Render services

1. Sign in to Render and choose **New + → Blueprint**.
2. Connect the GitHub repository and select the `main` branch.
3. Confirm Render finds `render.yaml`, then create the Blueprint.
4. Wait for both `hridaya-ai-api` and `hridaya-ai-web` to finish their first
   deploy. The API health check is `/health`; it returns 200 only after the
   model registry has loaded.
5. Open the static site's `onrender.com` URL and copy its origin only
   (for example, `https://hridaya-ai-web.onrender.com`; do not add a path or
   trailing slash).
6. In the `hridaya-ai-api` service, open **Environment**, add
   `ALLOWED_ORIGIN` with that exact static-site origin, save, and wait for the
   API redeploy to finish. The frontend/API host is wired automatically;
   this CORS origin is the only manual service setting.
7. Open the static site in a private/incognito window and verify the dashboard
   loads without CORS errors. Test `/health`, sample loading, predictions,
   SHAP, metrics/figures, and what-if suggestions.

Render web services may sleep on the free plan and need time to wake on the
first request. If the API deploy fails or restarts for memory use, inspect its
Render logs; the fitted models and SHAP runtime may require a larger API
instance.

## Environment variables

| Service | Variable | Value |
| --- | --- | --- |
| API | `PYTHON_VERSION` | Set to `3.14.0` in `render.yaml` |
| API | `ALLOWED_ORIGIN` | Exact `https://` origin of the deployed static site |
| Static site | `VITE_API_HOST` | Populated from the API service host by `render.yaml` |

Do not commit real `.env` files, credentials, or the local UCI dataset. For
local frontend development, copy `frontend/.env.example` to `frontend/.env`.

## Troubleshooting

- **API health check fails:** check the service logs and confirm the registry
  and its JSON sidecars were pushed. `/health` returns 503 until artifacts load.
- **Browser reports CORS:** make sure `ALLOWED_ORIGIN` exactly matches the
  static site's origin, then save and wait for the API redeploy.
- **Frontend calls localhost:** confirm `VITE_API_HOST` is present on the
  static site and trigger a new static-site deploy after changing it.
- **API restarts or is killed:** check memory in Render logs and upgrade the
  API service instance if needed.
