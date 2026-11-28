#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

spec="$(mktemp --suffix=.json)"
trap 'rm -f "$spec"' EXIT
(cd "$SERVER_DIR" && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi()))") > "$spec"
cd "$WEB_DIR"
pnpm exec openapi-typescript "$spec" --output src/lib/api/schema.d.ts
