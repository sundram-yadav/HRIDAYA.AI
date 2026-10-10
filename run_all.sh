#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000 &
cd frontend
npm install
npm run dev
