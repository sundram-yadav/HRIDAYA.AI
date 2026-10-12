@echo off
setlocal

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js 20.19+ and npm are required. Install Node.js and rerun this script.
  exit /b 1
)

if not exist models\registry.joblib (
  echo Trained artifacts are missing. Training from the local dataset...
  python -m ml.run_all
  if errorlevel 1 exit /b 1
)
if not exist models\metrics.json (
  echo Metrics are missing. Training from the local dataset...
  python -m ml.run_all
  if errorlevel 1 exit /b 1
)

start "Hriday API" cmd /k "call .venv\Scripts\activate && uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000"

cd frontend
if not exist node_modules (
  npm ci
)
npm run dev
