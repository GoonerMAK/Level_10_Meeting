# Level 10 Meeting

| Area | Path |
|---|---|
| Spec, seed, report format | `assessment/` |
| Infra (Postgres, env) | `docker-compose.yml`, `.env.example` |
| Server (uv, FastAPI, SQLAlchemy async) | `server/app/` |
| Business rules (pure functions, brief 2.6) | `server/app/calculations/` |
| Feature modules (router, schemas, service) | `server/app/modules/` |
| Migrations | `server/alembic/versions/` |
| Dev scripts | `tools/` |
| Backlog, in build order | GitHub issues #7–#25, each opens with an **Order:** line |
| Plugins + cloud setup hook | `.claude/settings.json` |

Run in order: `tools/db-up.sh` (start DB), `tools/db-migrate.sh` (migrate + drift check), `tools/seed.sh` (rerunnable), `tools/server.sh` (API on port 8000, reload). Tests: `tools/test.sh` (own `level10_test` DB; CI runs the same).

Cloud sessions: `tools/cloud-setup.sh` runs at start (Postgres without Docker on 5432, `.env`, migrate, seed). Working rules come from the mak-kit plugin.

Rules:
- Dev DB is container `level_10_meeting-db-1` on port 5434. Never stop other projects' containers on 5432 or 5433.

Reply format: Leverage i-have-adhd skill and caveman ultra skill, cite code inline as plain `path:line` when needed; no [text](link), no #L.
