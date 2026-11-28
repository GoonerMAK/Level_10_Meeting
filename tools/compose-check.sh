#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

web="http://localhost:${WEB_PORT:-3000}"
api="http://localhost:${API_PORT:-8000}"
compose=(docker compose -p level10-compose-check)
cookies=$(mktemp)

finish() {
  status=$?
  if [ "$status" -ne 0 ]; then
    "${compose[@]}" ps --all
    "${compose[@]}" logs --no-color
  fi
  "${compose[@]}" down --volumes --remove-orphans
  rm -f "$cookies"
  exit "$status"
}
trap finish EXIT

fetch() {
  curl --fail --silent --show-error --retry 30 --retry-delay 2 --retry-all-errors --cookie "$cookies" --cookie-jar "$cookies" "$@"
}

read_json() {
  node -p "const data = JSON.parse(require('fs').readFileSync(0)); $1"
}

"${compose[@]}" up --build --detach

fetch "$api/docs" > /dev/null
fetch "$web/sign-in" > /dev/null

seeded_users=$(read_json "data.users.length" < assessment/seed.json)
listed_users=$(fetch "$web/api/auth/users" | read_json "data.length")
if [ "$listed_users" != "$seeded_users" ]; then
  echo "Expected $seeded_users seeded users through the web app, got $listed_users" >&2
  exit 1
fi

fetch "$web/api/auth/sign-in" --header "Content-Type: application/json" --data '{"user_id": "u1"}' > /dev/null
signed_in_as=$(fetch "$web/api/auth/me" | read_json "data.id")
if [ "$signed_in_as" != "u1" ]; then
  echo "Expected to be signed in as u1, got $signed_in_as" >&2
  exit 1
fi

echo "docker compose up: API docs, sign-in page, $seeded_users seeded users and a sign-in through the web app all respond"
