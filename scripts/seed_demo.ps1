if (-not (docker compose ps -q api)) {
  docker compose up -d --build
}
$u = "http://localhost:8001"
for ($i=0; $i -lt 30; $i++) {
  try { Invoke-RestMethod "$u/healthz" | Out-Null; break } catch { Start-Sleep -Seconds 1 }
}
docker compose exec api python backend/scripts/seed_plus.py --reset --users 10 --missions 6 --days 14 --force-insert
