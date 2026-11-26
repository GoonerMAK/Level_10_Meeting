# Level 10 Meeting

| Area | Path |
|---|---|
| Spec, seed, report format | `assessment/` |
| Infra (Postgres, env) | `docker-compose.yml`, `.env.example` |
| Server (uv, SQLAlchemy async) | `server/app/` |
| Migrations | `server/alembic/versions/` |

Setup: `docker compose up -d --wait`, then in `server/` run `uv run alembic upgrade head` and `uv run python -m app.seed`.

Reply format: Leverage i-have-adhd skill and caveman ultra skill, cite code inline as plain `path:line` when needed; no [text](link), no #L.