# Personal Tracker — Build Plan

The phases below were built in order. Each one lists what was built and how "done" was checked.
Use the same format for future phases.

| Phase | What | Status |
|-------|------|--------|
| 0 | Setup: Docker Compose, FastAPI, Alembic, pytest, Vite | ✅ built |
| 1 | Auth: users, bcrypt, JWT cookie, login/register pages | ✅ built |
| 2 | Todos: CRUD, filters, sort, pagination, isolation | ✅ built |
| 3 | Finance: NUMERIC money, CRUD, filters, isolation | ✅ built |
| 4 | Stats + Home + Reminders | ✅ built |
| 4b | Enhancements: budget, repeat, CSV, email digest, dark mode, seed, rate limit | ✅ built |
| 5 | Deploy: production image, Render + Neon + Brevo, CI, daily cron | ✅ config built; **accounts are your part** |
| 6 | v2 ideas (see SPEC §9) | not started |

---

## Phase 0 — Setup
**Built:** folder structure, `docker-compose.yml` (db, backend, frontend, mailpit), FastAPI app,
settings from env, `.env.example`, Alembic, pytest with a separate test database, Vite + React + TS
with a dev proxy for `/api`.
**Done when:** `docker compose up` starts everything; `/api/health` returns 200; the frontend loads.

## Phase 1 — Auth
**Built:** User model + migration 0001; register/login/logout/me; bcrypt; JWT in an httpOnly
cookie; `get_current_user`; Login and Register pages; protected routes.
**Done when:** `tests/test_auth.py` passes; a logged-out visit to `/` redirects to `/login`.

## Phase 2 — Todos
**Built:** Todo model + migration 0002; repository/service/router; filters, sort, pagination,
toggle, repeat; the To-dos tab with a create/edit form and priority colours.
**Done when:** `tests/test_todos.py` passes including the isolation test; CRUD works in the UI.

## Phase 3 — Finance
**Built:** FinanceEntry with `amount NUMERIC(12,2)` + migration 0003; CRUD, filters, mark paid,
repeat, CSV export; the Finance entries tab.
**Done when:** `tests/test_finances.py` passes; 199.99 is shown as exactly 199.99.

## Phase 4 — Stats, Home, Reminders
**Built:** `/api/finances/stats`, `/api/home`, `/api/reminders`; charts; Home page (urgent todos,
month summary, budget bar, bills due in 7 days); Reminders page.
**Done when:** `tests/test_home.py` and `tests/test_reminders.py` pass; stats match a manual sum.

## Phase 4b — Enhancements
**Built:** monthly budget (migration 0004), email digest (console/SMTP/Brevo senders, Mailpit
locally, idempotent daily job), repeat-next-period, CSV export with formula-injection guard,
search, dark mode, login rate limit, delete account, demo seed script.

## Phase 5 — Deploy
**Built:** root `Dockerfile` (multi-stage: Node builds the SPA, Python serves API + SPA),
migrations on start, `render.yaml`, GitHub Actions CI and the daily reminder workflow,
`docs/DEPLOY.md` checklist.
**Your part:** create the GitHub repo, Neon database, Brevo account and Render service; paste the
environment variables; add the two GitHub secrets. Follow `docs/DEPLOY.md` step by step.
**Done when:** you can register and use the app at a public HTTPS URL, and the "Daily reminders"
workflow run sends you an email.
