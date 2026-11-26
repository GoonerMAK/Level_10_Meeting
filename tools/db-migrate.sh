#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "$SERVER_DIR"
uv run alembic upgrade head
uv run alembic check
