#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

cd "$REPO_ROOT"
docker compose -f docker-compose.yml -f compose.dev.yml up -d --wait db
