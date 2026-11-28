# Level 10 Meeting

| Area | Path |
|---|---|
| Setup, tests, assumptions, limitations, AI use | `README.md` |
| Decision record (brief 2.8), written at the end | `DECISIONS.md` |
| Spec, seed, report format | `assessment/` |
| Rules report output, checked in CI | `rules_report.json` |
| CI (server, web, two-browser, compose) | `.github/workflows/ci.yml` |
| Infra (full stack, env) | `docker-compose.yml` (db, migrate, server, web), `compose.dev.yml` (publishes the DB for local tools), `.env.example` |
| Server (uv, FastAPI, SQLAlchemy async) | `server/app/` |
| Business rules (pure functions, brief 2.6) | `server/app/calculations/` |
| Feature modules (router, schemas, service) | `server/app/modules/` |
| Migrations | `server/alembic/versions/` |
| Server tests (pytest, random order, seed check) | `server/tests/` |
| Web app (Next.js 16, shadcn, TanStack Query, pnpm) | `web/src/` (`app/` routes, `components/`, `lib/api/` typed client, `lib/live/` WebSocket) |
| Two-browser test and failure artifact | `web/e2e/` |
| Dev scripts | `tools/` |
| Backlog, in build order | GitHub issues #7–#25, each opens with an **Order:** line |
| Plugins + cloud setup hook | `.claude/settings.json` |

Run in order: `tools/db-up.sh` (start DB), `tools/db-migrate.sh` (migrate + drift check), `tools/seed.sh` (rerunnable), `tools/server.sh` (API on port 8000, reload), `tools/web.sh` (web on port 3000, proxies `/api` and the WebSocket to 8000). Tests: `tools/test.sh` (own `level10_test_<checkout hash>` DB per checkout, so worktrees never share one; `TEST_DATABASE_NAME` overrides; CI runs the same); web: `pnpm --dir web test`, `pnpm --dir web typecheck`, `pnpm --dir web lint`. After an API change: `tools/web-api-types.sh` regenerates `web/src/lib/api/schema.d.ts`. Rules report: `tools/report.sh > rules_report.json` (own throwaway DB). Full stack check: `tools/compose-check.sh` (own compose project, removed after; CI runs it).

Cloud sessions: `tools/cloud-setup.sh` runs at start (Postgres without Docker on 5432, `.env`, migrate, seed). Working rules come from the mak-kit plugin.

Rules:
- Dev DB is container `level_10_meeting-db-1` on port 5434. Never stop other projects' containers on 5432 or 5433.

Reply format: Leverage i-have-adhd skill and caveman ultra skill, cite code inline as plain `path:line` when needed; no [text](link), no #L.
