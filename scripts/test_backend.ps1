docker compose exec api python -c "import pytest, httpx; print('deps-ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker compose exec api python -m pytest -q
