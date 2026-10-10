@echo off
setlocal

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

start "Hriday API" cmd /k "call .venv\Scripts\activate && uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000"

cd frontend
if not exist node_modules (
  npm install
)
npm run dev
