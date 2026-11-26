# Level 10 Meeting

| Area | Path |
|---|---|
| Spec, seed, report format | `assessment/` |
| Infra (Postgres, env) | `docker-compose.yml`, `.env.example` |
| Server (uv, SQLAlchemy async) | `server/app/` |
| Migrations | `server/alembic/versions/` |
| Dev scripts | `tools/` |

Run in order: `tools/db-up.sh` (start DB), `tools/db-migrate.sh` (migrate + drift check), `tools/seed.sh` (rerunnable). Tests: `tools/test.sh` (own `level10_test` DB; CI runs the same).

Rules:
- Dev DB is container `level_10_meeting-db-1` on port 5434. Never stop other projects' containers on 5432 or 5433.

Reply format: Leverage i-have-adhd skill and caveman ultra skill, cite code inline as plain `path:line` when needed; no [text](link), no #L.
