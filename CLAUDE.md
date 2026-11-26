# Level 10 Meeting

| Area | Path |
|---|---|
| Spec, seed, report format | `assessment/` |
| Infra (Postgres, env) | `docker-compose.yml`, `.env.example` |
| Server (uv, SQLAlchemy async) | `server/app/` |
| Migrations | `server/alembic/versions/` |
| Dev scripts, below | `tools/` |

| Script | Does |
|---|---|
| `tools/db-up.sh` | Starts Postgres, waits until healthy |
| `tools/db-migrate.sh` | `alembic upgrade head`, then `alembic check` for drift |
| `tools/seed.sh` | Loads `seed.json`; safe to rerun |

Rules:
- Dev DB is container `level_10_meeting-db-1` on port 5434. Never stop other projects' containers on 5432 or 5433.

Reply format: Leverage i-have-adhd skill and caveman ultra skill, cite code inline as plain `path:line` when needed; no [text](link), no #L.
