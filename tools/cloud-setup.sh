#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

as_root() {
  if [ "$(id -u)" = "0" ]; then "$@"; else sudo "$@"; fi
}

as_postgres() {
  as_root su postgres -c "$1"
}

if ! command -v pg_ctlcluster >/dev/null; then
  as_root apt-get update -qq
  DEBIAN_FRONTEND=noninteractive as_root apt-get install -y -qq postgresql >/dev/null
fi
as_root service postgresql start >/dev/null

if ! as_postgres "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname = 'level10'\"" | grep -q 1; then
  as_postgres "psql -c \"CREATE ROLE level10 LOGIN PASSWORD 'level10' CREATEDB\""
fi
if ! as_postgres "psql -tAc \"SELECT 1 FROM pg_database WHERE datname = 'level10'\"" | grep -q 1; then
  as_postgres "psql -c \"CREATE DATABASE level10 OWNER level10\""
fi

if [ ! -f "$REPO_ROOT/.env" ]; then
  cat > "$REPO_ROOT/.env" <<'ENV'
POSTGRES_USER=level10
POSTGRES_PASSWORD=level10
POSTGRES_DB=level10
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://level10:level10@localhost:5432/level10
ENV
fi
if ! grep -q '^SESSION_SECRET=' "$REPO_ROOT/.env"; then
  echo "SESSION_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> "$REPO_ROOT/.env"
fi

command -v uv >/dev/null || python3 -m pip install --quiet uv

cd "$SERVER_DIR"
uv sync --locked --quiet
uv run alembic upgrade head
uv run python -m app.seed >/dev/null
