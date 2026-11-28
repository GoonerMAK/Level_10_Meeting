#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "$SERVER_DIR"
uv run pytest "$@"

cd "$WEB_DIR"
pnpm install --frozen-lockfile
pnpm test
pnpm exec playwright install chromium
pnpm exec playwright test
