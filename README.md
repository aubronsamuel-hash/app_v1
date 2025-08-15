# app_v1
Backend: FastAPI minimal.

## Run with Docker
powershell:
  scripts\\dev_up.ps1
  scripts\\test_backend.ps1
  scripts\\dev_down.ps1

Manual (no Docker):
  python -m venv .venv
  . .\\.venv\\Scripts\\Activate.ps1
  pip install -r backend\\requirements.txt
  pytest -q
  uvicorn app.main:app --host 0.0.0.0 --port 8001
