# Duely (Todo + Finance) — Spec

This is the source of truth for what gets built. If anything else disagrees with this file, this file wins.

## 1. Purpose

A public web app for managing todos and personal finances. Anyone can sign up; each user sees only their own data.

It is also a learning and portfolio project: every part should be explainable (see §11 and `docs/GUIDE.md`).

## 2. Stack

| Layer      | Choice                                                                 |
|------------|------------------------------------------------------------------------|
| Frontend   | React + TypeScript (strict) + Vite, React Router, TanStack Query, Recharts |
| Backend    | Python 3.12, FastAPI, Pydantic v2                                      |
| ORM        | SQLAlchemy 2.0 (typed style, **sync**)                                 |
| Migrations | Alembic. `create_all` is never used.                                   |
| Database   | PostgreSQL 16                                                          |
| Auth       | JWT (PyJWT) in an httpOnly cookie; passwords hashed with bcrypt        |
| Email      | Pluggable sender: console (default), SMTP (Mailpit locally), Brevo HTTP API (production) |
| Dev env    | Docker Compose: db, backend, frontend, mailpit                         |
| Prod       | One Docker image (API + built SPA) on Render, Neon Postgres, GitHub Actions for CI and the daily reminder trigger |
| Tests      | pytest against a real test Postgres (backend); Vitest (frontend)       |

## 3. Shared fields (fixed names, used everywhere)

| Field      | Values                             | Meaning                                         |
|------------|------------------------------------|-------------------------------------------------|
| `period`   | `daily`, `monthly`, `yearly`       | A label. Not a repeat rule (see FR10 "repeat"). |
| `priority` | `high`, `medium`, `low`            |                                                 |
| `category` | `home`, `office`, `self`, `misc`   |                                                 |

## 4. Domain model

```
User
  id, email (unique, stored lowercase), password_hash, name, created_at
  monthly_budget?        NUMERIC(12,2)
  email_reminders        bool, default false
  last_reminder_sent_on? date   -- makes the daily job safe to run twice

Todo
  id, user_id FK -> User (ON DELETE CASCADE)
  title, description?, period, priority, category
  due_date?, completed (bool), completed_at?
  created_at, updated_at
  index (user_id, due_date)

FinanceEntry
  id, user_id FK -> User (ON DELETE CASCADE)
  title, description?, period, priority, category
  kind: expense | income
  amount: NUMERIC(12,2), > 0   -- never float
  entry_date                   -- when it happened, or when it is due
  status: planned | paid
  created_at, updated_at
  index (user_id, entry_date)
```

- **Currency:** one currency, set in config. Default INR.
- **Time zone:** "today" is computed in `APP_TIMEZONE` (default `Asia/Kolkata`).
- **Stats and budget** count only `paid` entries.

## 5. Features

**FR1 — Auth**
- Register (logs you in), login, logout, me, update profile, delete account.
- bcrypt password hashing. Password 8–72 bytes.
- JWT in an httpOnly cookie: `SameSite=Lax`, `Secure` in production, 24-hour expiry. No refresh token.
- Rate limits (→ 429): failed logins 5 per email and 20 per IP per 15 minutes; sign-ups 5 per IP
  per hour; test email 1 per 10 minutes and 5 per day per user, 100 per day for the whole app.
- Request bodies over 64 KB → 413; chunked bodies without a length → 411.
- Production: Content-Security-Policy, HSTS, and no `/docs` or `/openapi.json`.

**FR2 — Data isolation**
- Every todo/finance query is filtered by the current user.
- Requesting another user's record returns 404.

**FR3 — Todo CRUD**
- Create, read, update (PUT), delete, toggle complete, repeat next period.
- Filters: `period`, `priority`, `category`, `completed`, `due_from`/`due_to`, `q` (title search).
- Sort by `due_date`, `priority`, `created_at`, `title`; `order` asc/desc.
- Paginate with `limit` (1–100) / `offset`. Response: `{ items, total, limit, offset }`.

**FR4 — Finance CRUD**
- Same as todos, plus filters `kind`, `status`, `date_from`/`date_to`; sort by `entry_date`, `amount`, `priority`, `created_at`.
- Mark paid. Repeat next period.
- CSV export of the filtered list (spreadsheet formula injection is neutralised).

**FR5 — Finance stats**
- `GET /api/finances/stats?date_from&date_to` (default: current calendar year) returns
  total income, total expense, net, totals by category (all four, zeros included),
  totals by month (every month in range, zeros included).

**FR6 — Home**
- `GET /api/home` returns: urgent todos (incomplete AND (priority high OR due today or overdue)),
  this month's summary with budget usage, planned payments due in the next 7 days, and counts
  (open, overdue, completed this week).

**FR7 — Reminders**
- `GET /api/reminders`: overdue / due today / next 7 days, for todos and planned payments.
- Reminders page shows these lists and the email reminder setting.
- `POST /api/reminders/test-email` emails the current user their digest now.
- `POST /api/internal/reminders/run` (header `X-Cron-Secret`) emails every opted-in user who has
  something due and has not had a digest today. Triggered daily by GitHub Actions.

**FR8 — UI pages**
- Login / Register
- Home: urgent todos, month summary + budget bar, upcoming payments
- Dashboard: tabs **To-dos** and **Finance** (Finance has **List** and **Stats** views with charts)
- Reminders
- Settings: name, monthly budget, email reminders, delete account
- Priority colours: high = red, medium = amber, low = green, always with a text label.
- Light/dark theme toggle (stored in the browser).

**FR9 — Demo data**
- `python -m app.scripts.seed_demo` creates a demo user with sample todos and finances.

**FR10 — Repeat next period**
- Copies an item with its date moved forward by its period: +1 day, +1 month (clamped to month
  end), +1 year. A todo copy starts incomplete; a finance copy starts `planned`.

## 6. API

| Method | Path                              | Notes                          |
|--------|-----------------------------------|--------------------------------|
| POST   | /api/auth/register                | sets the cookie, 201           |
| POST   | /api/auth/login                   | sets the cookie                |
| POST   | /api/auth/logout                  | clears the cookie, 204         |
| GET    | /api/auth/me                      |                                |
| PATCH  | /api/auth/me                      | name, monthly_budget, email_reminders |
| DELETE | /api/auth/me                      | deletes account and data, 204  |
| GET    | /api/todos                        | filters, sort, pagination      |
| POST   | /api/todos                        | 201                            |
| GET    | /api/todos/{id}                   |                                |
| PUT    | /api/todos/{id}                   |                                |
| PATCH  | /api/todos/{id}/toggle            |                                |
| POST   | /api/todos/{id}/repeat            | 201                            |
| DELETE | /api/todos/{id}                   | 204                            |
| GET    | /api/finances                     | filters, sort, pagination      |
| POST   | /api/finances                     | 201                            |
| GET    | /api/finances/stats               |                                |
| GET    | /api/finances/export.csv          | same filters as list           |
| GET    | /api/finances/{id}                |                                |
| PUT    | /api/finances/{id}                |                                |
| PATCH  | /api/finances/{id}/pay            |                                |
| POST   | /api/finances/{id}/repeat         | 201                            |
| DELETE | /api/finances/{id}                | 204                            |
| GET    | /api/home                         |                                |
| GET    | /api/reminders                    |                                |
| POST   | /api/reminders/test-email         |                                |
| POST   | /api/internal/reminders/run       | `X-Cron-Secret` header         |
| GET    | /api/health                       | also checks the database       |

## 7. Non-functional rules

- **Money** is NUMERIC/Decimal end to end; JSON carries it as a string ("199.99"). The UI formats strings without float arithmetic.
- **Errors** return JSON `{ "detail": ... }` with correct status codes.
- **Secrets** come only from environment variables.
- **CORS** allows only the frontend origin (in production the SPA is same-origin).
- **Schema changes** only through Alembic migrations; `alembic check` runs in CI.
- **Tests:** every endpoint has tests; every resource has an isolation test.

## 8. Out of scope

- Recurring engine (automatic repeats), multi-currency, sharing, audit history, mobile app, SMS/push.

## 9. Possible v2

- Web push notifications, recurring rules, audit history, password reset by email, receipt uploads.

## 10. Deployment summary

See `docs/DEPLOY.md`.

## 11. Concepts to understand by the end

See `docs/GUIDE.md`.
