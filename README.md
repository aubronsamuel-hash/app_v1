# app_v1
Backend: FastAPI minimal.

## Run with Docker
powershell:
  scripts\dev_up.ps1
  scripts\test_backend.ps1
  scripts\dev_down.ps1

Manual (no Docker):
  python -m venv .venv
  . .\.venv\Scripts\Activate.ps1
  pip install -r backend\requirements.txt
  pytest -q
  uvicorn app.main:app --host 0.0.0.0 --port 8001

## Auth quickstart
powershell:
  $u = "http://localhost:8001"
  Invoke-RestMethod -Uri "$u/auth/register" -Method Post -Body (@{username='alice';password='secret'} | ConvertTo-Json) -ContentType "application/json"
  $tok = Invoke-RestMethod -Uri "$u/auth/token-json" -Method Post -Body (@{username='alice';password='secret'} | ConvertTo-Json) -ContentType "application/json"
  Invoke-RestMethod -Uri "$u/auth/me" -Headers @{Authorization="Bearer $($tok.access_token)"}

curl:
  u=http://localhost:8001
  curl -X POST "$u/auth/register" -H "Content-Type: application/json" -d '{"username":"alice","password":"secret"}'
  tok=$(curl -s -X POST "$u/auth/token-json" -H "Content-Type: application/json" -d '{"username":"alice","password":"secret"}' | jq -r .access_token)
  curl "$u/auth/me" -H "Authorization: Bearer $tok"
