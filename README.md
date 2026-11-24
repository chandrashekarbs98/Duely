# Duely

Tasks and money, on time. To-dos, bills and reminders in one place: a full-stack web app built with **React + TypeScript**,
**FastAPI**, **PostgreSQL** and **Docker**, deployed to the cloud.

**Live demo:** _add your Render URL here after deploying_ · Demo login: _see docs/DEPLOY.md step 6_

## Features

- **Accounts**: sign up, log in (JWT in an httpOnly cookie), profile, delete account
- **Home**: urgent to-dos, this month's income/spend/net, budget progress, bills due this week
- **To-dos**: daily/monthly/yearly, high/medium/low priority, home/office/self/misc; search,
  filter, sort, paginate; complete; *repeat next period*
- **Finance**: expenses and income, paid or planned, exact decimal money, mark paid, repeat
  (subscriptions), CSV export
- **Charts**: monthly income vs expense, spending by type, any date range
- **Reminders**: overdue / today / next 7 days; opt-in daily email digest
- Dark mode, mobile layout, accessible (labels, keyboard, colour + text)

## Tech stack

React 19 · TypeScript (strict) · Vite · React Router · TanStack Query · Recharts ·
FastAPI · Pydantic v2 · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 · PyJWT · bcrypt ·
Docker Compose · GitHub Actions · Render · Neon · Brevo · pytest · Vitest

## Architecture

```
Browser ──HTTPS──▶ one container: FastAPI ── /api/* → routers → services → repositories ──▶ Postgres
                                          └─ /*     → built React app
GitHub Actions: CI on every push · daily cron → /api/internal/reminders/run → email
```

## Run it locally

Requirements: Docker Desktop.

```bash
cp .env.example .env            # then set JWT_SECRET and CRON_SECRET to long random strings
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_demo --password demo-password-123
```

| URL | What |
|-----|------|
| http://localhost:5173 | The app (log in as `demo@example.com` / `demo-password-123`) |
| http://localhost:8000/docs | Interactive API docs |
| http://localhost:8025 | Mailpit: every email the app sends locally |

## Tests and checks

```bash
docker compose exec backend pytest            # 59 backend tests on a real Postgres
docker compose exec backend alembic check     # models match migrations
docker compose exec backend ruff check . && docker compose exec backend black --check .
cd frontend && npm test && npm run lint && npm run build
```

## Documentation

| File | For |
|------|-----|
| [docs/GUIDE.md](docs/GUIDE.md) | **Study guide**: how and why everything works, with interview questions |
| [docs/SPEC.md](docs/SPEC.md) | What the app does (source of truth) |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Deploying to Render + Neon + Brevo, checklist, troubleshooting |
| [docs/PLAN.md](docs/PLAN.md) | Build phases and their done criteria |
