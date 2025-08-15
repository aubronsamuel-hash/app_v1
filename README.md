# app_v1

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)

Backend: FastAPI minimal.

## CI

Continuous Integration runs backend tests with `python -m pytest -q` on pushes and pull requests.

## CI Front

[![CI Front](https://github.com/OWNER/REPO/actions/workflows/ci_front.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci_front.yml)

Runs frontend typecheck, lint, and build, uploading `dist` as artifact.

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

## Frontend
Docker:
  docker compose up -d --build
  browse http://localhost:5173

Local:
  cd frontend
  npm i
  npm run dev

Set `VITE_API_URL` to point to the API (defaults to http://localhost:8001). Token persists in `localStorage`.

## Environment variables
- `DATA_DIR`: path for JSON storage (default `./data` with Docker)
- `CORS_ORIGINS`: comma-separated origins for CORS, `*` allows all (default `*`)
- `TOKEN_TTL`: token expiration in minutes (default `1440`)

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

## Missions
powershell:
  $u = "http://localhost:8001"
  Invoke-RestMethod -Uri "$u/missions"
  $m = @{title="Show";start="2025-08-16T08:00:00Z";end="2025-08-16T12:00:00Z";positions=@()} | ConvertTo-Json
  Invoke-RestMethod -Uri "$u/missions" -Method Post -Headers @{Authorization="Bearer $tok"} -Body $m -ContentType "application/json"

curl:
  u=http://localhost:8001
  curl "$u/missions"
  curl -X POST "$u/missions" -H "Authorization: Bearer $tok" -H "Content-Type: application/json" -d '{"title":"Show","start":"2025-08-16T08:00:00Z","end":"2025-08-16T12:00:00Z","positions":[]}'

Note: POST/PUT/DELETE /missions endpoints require a Bearer token.

## Seeding demo
powershell:
  scripts\seed_demo.ps1
bash:
  docker compose up -d --build
  docker compose exec api python backend/scripts/seed_plus.py --reset --users 10 --missions 6 --days 14 --force-insert

## Notifications
- `PUT /auth/me/prefs` (Bearer) store notification preferences `{email, telegram, telegram_chat_id}`
- `POST /auth/me/notify-test` (Bearer) test notification channels; returns `{ok,dry_run,channels}`
- `GET /admin/notifications/diagnostic` (admin) count users with prefs
- `POST /admin/notifications/diagnostic/test` (admin) dry-run test for all users

## Backup/Restore
- `GET /admin/backup` (admin) download JSON backup
- `POST /admin/restore?wipe=true|false` (admin) restore from JSON; `wipe=false` merges
powershell:
  $env:TOKEN = "...admin token..."
  scripts\backup.ps1
  scripts\restore.ps1 -File backup_20240101_000000.json
  scripts\restore.ps1 -File backup_20240101_000000.json -NoWipe
