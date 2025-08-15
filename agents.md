Goal: add an Agents guide file at repo root so future Codex tasks have all context.

Branch: create "chore/agents-md".

Constraints:
- ASCII only.
- Do not break existing code or tests.
- Keep current docker-compose.yml and backend as-is.

1) Create/overwrite AGENTS.md at repo root with the exact content below (ASCII). Also create "agent.md" with the same content.

=== AGENTS.md (BEGIN) ===
# AGENTS GUIDE (app_v1)

Purpose: give Codex agents everything needed to run, test, and contribute safely.

## Repo layout
- backend/ : FastAPI app (app/main.py, routers/, storage.py, schemas.py)
- backend/tests/ : pytest tests
- docker-compose.yml : dev stack
- scripts/ : PowerShell helpers for Windows
- data/ : runtime JSON data (persisted via Docker volume)

## Runtime
- API port: 8001 (host)
- Data directory: /data (inside container), mapped to ./data on host
- Health endpoint: GET /healthz -> {"status":"ok"}

## Python requirements (backend/requirements.txt)
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.8.2
pytest==8.2.0
bcrypt==4.1.3
httpx==0.27.0

## Local commands (Windows PowerShell)
scripts\\dev_up.ps1
scripts\\test_backend.ps1
scripts\\dev_down.ps1

Smoke test:
Invoke-RestMethod http://localhost:8001/healthz

## Local commands (bash)
docker compose up -d --build
docker compose exec api python -m pytest -q
docker compose down -v
curl -s http://localhost:8001/healthz

## Environment variables
- DATA_DIR (optional): overrides /data path inside API container.
- VITE_API_URL (reserved for future frontend).

## Storage model (JSON at /data/data.json)
{
  "users": [
    {"id": 1, "username": "admin", "password_hash": "...", "role": "intermittent", "is_active": true}
  ],
  "tokens": [
    {"token": "tok_...", "user_id": 1, "created_at": "ISO8601"}
  ]
}

## Coding rules
- ASCII only in scripts and filenames.
- Error messages simple, stable.
- Add/modify tests for every feature.
- Keep /healthz unchanged.

## Task policy for Codex
- Branch naming: codex/<short-topic> or feat/... / chore/... / fix/...
- For each task:
  1) Detect environment (Docker, ports, requirements).
  2) Run tests: "pytest -q". If red, fix only within task scope.
  3) Make minimal changes, keep backward compatibility.
  4) Update README when new endpoints or commands are added.
  5) Open a PR with a clear title and summary, list test results.

## Network policy for Codex agent
- Network during setup: ON (to install deps).
- Network during task: OFF (unless explicitly allowed).

## Conventional commits (recommended)
feat: new user-facing feature
fix: bug fix
chore: tooling/docs/infra
test: tests only
refactor: no feature change
docs: docs only
ci: CI changes

## Quick API examples (PowerShell)
$u = @{ username="admin"; password="admin" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8001/auth/register -Method Post -Body $u -ContentType "application/json"
$t = Invoke-RestMethod -Uri http://localhost:8001/auth/token-json -Method Post -Body $u -ContentType "application/json"
$hdr = @{ Authorization = "Bearer $($t.access_token)" }
Invoke-RestMethod -Uri http://localhost:8001/auth/me -Headers $hdr

## Do and Do not (for agents)
DO:
- Keep tests green (pytest -q).
- Persist changes in JSON via storage.py.
- Add small, focused PRs.

DO NOT:
- Introduce new heavy dependencies without need.
- Remove healthz or change ports.
- Commit secrets or non-ASCII files.

# End of guide.
=== AGENTS.md (END) ===

2) Create "agent.md" at repo root with the same content as AGENTS.md.

3) Run tests:
- Command: python -m pytest -q
- All tests must pass.

4) Open a PR titled:
chore: add AGENTS.md (agents guide) for Codex tasks

Deliverables:
- AGENTS.md (repo root)
- agent.md (repo root)
- No code regressions, tests green.
