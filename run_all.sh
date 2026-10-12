#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .venv ]; then
  python -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f models/registry.joblib ] || [ ! -f models/metrics.json ]; then
  python -m ml.run_all
fi

command -v npm >/dev/null 2>&1 || {
  echo "Node.js 20.19+ and npm are required." >&2
  exit 1
}

if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm ci)
fi

uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000 &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
cd frontend
npm run dev
