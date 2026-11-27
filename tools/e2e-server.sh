#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "$SERVER_DIR"
DATABASE_URL="$(uv run python -m app.db.fresh e2e)"
export DATABASE_URL
exec uv run uvicorn app.main:app --port "$1"
