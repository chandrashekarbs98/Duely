# Duely — Study Guide

This guide explains **how the app is built and why**. Read it top to bottom once, then use it as a
reference. File paths are clickable in most editors. Each section ends with **Check yourself**
questions; if you can answer them without looking, you understand that part.

Contents
1. What was built
2. The big picture (architecture)
3. Tour of the repository
4. One request, end to end
5. Backend layers: routers → services → repositories
6. Authentication and authorization
7. Data isolation
8. The database: models, constraints, money, migrations
9. Pydantic vs SQLAlchemy vs PostgreSQL: who does what
10. API design
11. The frontend
12. Reminders: schedulers, webhooks and email
13. Testing strategy
14. Docker
15. Deployment and the cloud
16. Security checklist
17. Design decisions and trade-offs
18. How to extend it (worked example)
19. Interview questions
20. Resume bullets
21. Glossary

---

## 1. What was built

A public web app where anyone can sign up and keep **to-dos** and **personal finances**, each user
seeing only their own data.

| Area | Features |
|------|----------|
| Accounts | Register, log in/out, profile, monthly budget, delete account, login rate limit |
| Home | Urgent to-dos (high priority, due today or overdue), this month's income/spend/net, budget progress bar, bills due in 7 days, counters |
| Dashboard → To-dos | Create/edit/delete, complete, **repeat next period**, search, filter by period/priority/type/status, sort, paginate |
| Dashboard → Finance | Expenses and income, paid or planned, exact money, mark paid, repeat (subscriptions), filters, **CSV export** |
| Dashboard → Charts | Income vs expense per month, spending by type, totals for a chosen range |
| Reminders | Overdue / due today / next 7 days for to-dos and bills; opt-in **daily email digest**; "send test email" |
| Everywhere | Light/dark theme, mobile layout, keyboard and screen-reader friendly |

Shared vocabulary (SPEC §3): `period` = daily/monthly/yearly, `priority` = high/medium/low,
`category` ("type" in the UI) = home/office/self/misc.

### Tech stack and why each piece

| Layer | Tool | Why |
|-------|------|-----|
| UI | **React 19 + TypeScript (strict)** | Component model; types catch mistakes at build time |
| Build/dev server | **Vite** | Instant dev server, proxies `/api` to the backend |
| Routing | **React Router 7** | URLs for pages (`/dashboard?tab=finance`) |
| Server state | **TanStack Query** | Caching, loading/error states, refetch after changes |
| Charts | **Recharts** | Declarative SVG charts for React |
| API | **FastAPI** | Type-hint driven, automatic validation and OpenAPI docs (`/docs`) |
| Validation | **Pydantic v2** | Parses and validates every request and response |
| ORM | **SQLAlchemy 2.0** (typed, sync) | Python classes ↔ tables; composable queries |
| Migrations | **Alembic** | Versioned, reviewable schema changes |
| Database | **PostgreSQL 16** | Reliable, `NUMERIC` for money, great indexes |
| Auth | **PyJWT + bcrypt** | Signed tokens; slow, salted password hashes |
| Email | console / **SMTP** (Mailpit) / **Brevo** API | Swap providers by config |
| Dev environment | **Docker Compose** | One command starts db, backend, frontend, mail catcher |
| Prod | **Render** + **Neon** + **Brevo** | Free tiers, HTTPS, managed Postgres |
| CI/CD | **GitHub Actions** | Tests on every push; daily reminder trigger |
| Quality | pytest, Vitest, ruff, black, eslint, prettier | Tests and consistent style |

---

## 2. The big picture

### Development (your laptop)

```
 Browser ──http://localhost:5173──▶ frontend container (Vite dev server, hot reload)
                                       │  /api/* is proxied
                                       ▼
                                   backend container (uvicorn --reload, FastAPI)
                                       │ SQL                     │ SMTP
                                       ▼                         ▼
                                   db container (Postgres)   mailpit (fake inbox, :8025)
                                   ├─ tracker       (dev data)
                                   └─ tracker_test  (pytest only)
```

### Production

```
 Browser ──https://your-app.onrender.com──▶ ONE container
                                             uvicorn → FastAPI
                                               /api/*  → API
                                               /*      → built React files
                                             │ SQL/TLS        │ HTTPS
                                             ▼                ▼
                                          Neon Postgres     Brevo email API
 GitHub Actions: CI on push; at 08:00 IST POSTs /api/internal/reminders/run
```

**Key idea:** in development the frontend and backend are separate servers (for hot reload). In
production they are **one origin**: FastAPI serves the built React files *and* the API. Section 15
explains why that matters for cookies.

**Check yourself:** Why are there two databases locally? What serves `index.html` in production?

---

## 3. Tour of the repository

```
TODO Project/
├─ backend/
│  ├─ app/
│  │  ├─ main.py            app factory: middleware, error mapping, serves SPA in prod
│  │  ├─ api/               ROUTERS — HTTP only (paths, status codes, cookies)
│  │  │   auth.py todos.py finances.py home.py reminders.py health.py router.py
│  │  ├─ services/          BUSINESS RULES — no HTTP, no SQL
│  │  │   auth.py todo.py finance.py home.py reminders.py dates.py
│  │  ├─ repositories/      ALL DATABASE QUERIES — the only code that uses the Session
│  │  │   user.py todo.py finance.py health.py
│  │  ├─ models/            SQLAlchemy tables (User, Todo, FinanceEntry, enums)
│  │  ├─ schemas/           Pydantic request/response shapes
│  │  ├─ core/              config, db engine, security, deps, email, clock, errors, rate limit
│  │  └─ scripts/seed_demo.py
│  ├─ alembic/versions/     0001 users → 0002 todos → 0003 finance → 0004 user settings
│  ├─ tests/                one file per router + conftest.py fixtures
│  ├─ Dockerfile            dev image (hot reload)
│  └─ pyproject.toml        dependencies + tool config
├─ frontend/
│  ├─ src/
│  │  ├─ api/               client.ts (the only place that calls fetch) + types.ts
│  │  ├─ auth/              AuthProvider (who is logged in) + route guards
│  │  ├─ components/        Layout, shared UI bits (Modal, badges, pagination)
│  │  ├─ features/todos/    To-dos tab, form, row
│  │  ├─ features/finance/  Entries list, form, row, charts
│  │  ├─ pages/             Home, Dashboard, Reminders, Settings, Login/Register
│  │  ├─ lib/               money, dates, labels, theme, query helpers
│  │  ├─ main.tsx App.tsx styles.css
│  └─ vite.config.ts        dev proxy /api → backend
├─ Dockerfile               PRODUCTION image (multi-stage)
├─ docker-compose.yml       local dev: db, mailpit, backend, frontend
├─ render.yaml              Render blueprint (infrastructure as code)
├─ .github/workflows/       ci.yml, reminders.yml
└─ docs/                    SPEC, PLAN, GUIDE (this), DEPLOY
```

---

## 4. One request, end to end

Let's follow **"Add an expense of ₹199.99"**. This is the most important section: every web app
works like this.

**1. The click** — [FinanceForm.tsx](../frontend/src/features/finance/FinanceForm.tsx) validates the
amount (`isValidMoneyInput`) and calls `onSubmit` with `amount: "199.99"` — a **string**.

**2. The mutation** — [FinanceList.tsx](../frontend/src/features/finance/FinanceList.tsx) runs
`useDataMutation(api.createFinance)`. TanStack Query tracks loading and error state for us.

**3. The API client** — [client.ts](../frontend/src/api/client.ts) calls
`fetch("/api/finances", { method: "POST", credentials: "include", body: JSON })`.
`credentials: "include"` tells the browser to attach the `access_token` cookie. JavaScript can't
read that cookie (httpOnly), but the browser still sends it.

**4. Reaching the server** — in dev, Vite's proxy ([vite.config.ts](../frontend/vite.config.ts))
forwards `/api/*` to `http://backend:8000`. In prod it's the same origin, so nothing to forward.

**5. Uvicorn → FastAPI** — uvicorn (the ASGI server) parses HTTP and hands the request to the
FastAPI app. Middleware runs first (CORS, security headers in [main.py](../backend/app/main.py)).
FastAPI matches `POST /api/finances` to `create_entry` in
[api/finances.py](../backend/app/api/finances.py).

**6. Dependencies** — before the function body runs, FastAPI resolves its parameters:
- `data: FinanceWrite` → Pydantic parses the JSON body. `"199.99"` becomes `Decimal("199.99")`.
  `"10.999"` or `"-5"` would be rejected here with **422**, before any of our code runs.
- `user: CurrentUser` → `get_current_user` in [core/deps.py](../backend/app/core/deps.py) reads
  the cookie, verifies the JWT signature and expiry, and loads the user. No valid token → **401**.
- `service: Service` → `get_finance_service` builds `FinanceService(FinanceRepository(db))`, where
  `db` comes from `get_db` (one Session per request, always closed).

**7. Router → service → repository** — the router calls `service.create(user, data)`; the service
calls `self.entries.create(user.id, data.model_dump())`; the repository
([repositories/finance.py](../backend/app/repositories/finance.py)) does
`db.add(entry); db.commit(); db.refresh(entry)`.

**8. SQL** — SQLAlchemy emits `INSERT INTO finance_entries (...) VALUES (...) RETURNING id, ...`.
Postgres checks the constraints (`amount > 0`, allowed `kind` values, the foreign key to `users`)
and stores `199.99` as `NUMERIC(12,2)`, exactly.

**9. The response** — the router returns `FinanceRead.model_validate(entry)`. FastAPI serializes it
with Pydantic; `Decimal` becomes the JSON string `"199.99"`. Status **201 Created**.

**10. Back in the browser** — the mutation's `onSuccess` invalidates cached queries; TanStack Query
refetches what's on screen (the list, and Home/Stats next time you visit), and React re-renders.
The amount is shown by `formatMoney("199.99", "INR")` → `₹199.99`, using string digits, not floats.

**Check yourself:** At which step would a request with an expired cookie fail? Which step rejects
`amount: "10.999"`? Who turns `Decimal` into a string?

---

## 5. Backend layers

```
 api/ (routers)        "HTTP": paths, verbs, status codes, cookies, query params
      │ calls
 services/             "rules": urgent = high OR due ≤ today; repeat = +1 period; budget %
      │ calls
 repositories/         "SQL": select/insert/update, always filtered by user_id
      │ uses
 SQLAlchemy Session ──▶ PostgreSQL
```

Why bother splitting?
- **Each layer has one reason to change.** Switching from cookies to headers touches routers only.
  Changing what "urgent" means touches one service. Adding an index touches no Python at all.
- **Testability.** Services don't know about HTTP, so the seed script
  ([seed_demo.py](../backend/app/scripts/seed_demo.py)) and the daily reminder job reuse them.
- **One place for security-critical filtering.** Every todo/finance query lives in a repository
  and every repository method takes `user_id` (section 7).

**Domain errors, not HTTP errors.** Services raise `NotFoundError`, `ConflictError`… from
[core/errors.py](../backend/app/core/errors.py). One exception handler in
[main.py](../backend/app/main.py) turns them into `{"detail": ...}` with the right status. So
services never import FastAPI.

**Dependency injection.** `Depends(...)` builds objects per request. Tests replace them with
`app.dependency_overrides` (e.g. the email sender becomes a fake that records emails).

**Sync, not async.** FastAPI runs `def` (sync) endpoints in a thread pool, so blocking database
calls don't freeze the server. Async SQLAlchemy adds complexity that pays off only at much higher
load. The rule (CLAUDE.md) is: pick one style and use it everywhere.

**Check yourself:** Where would you put "a user can have at most 500 open to-dos"? Why does the
service raise `NotFoundError` instead of `HTTPException(404)`?

---

## 6. Authentication and authorization

- **Authentication** = *who are you?* (login, the cookie, `get_current_user`)
- **Authorization** = *what may you touch?* (only your own rows: section 7)

### Passwords — [core/security.py](../backend/app/core/security.py)
- Never stored. We store `bcrypt(password)`: a **salted, deliberately slow** hash. Salt means two
  users with the same password get different hashes; slowness makes guessing expensive.
- bcrypt reads at most 72 bytes, so longer passwords are rejected instead of silently truncated.
- Failed login says "Invalid email or password" in both cases, and even for an unknown email we run
  bcrypt against a dummy hash so response time doesn't reveal which emails exist.

### Tokens — JWT
A JWT is `header.payload.signature`, base64-encoded. Our payload: `{"sub": "42", "iat": ..., "exp": ...}`.
The signature is HMAC-SHA256 with `JWT_SECRET`. Anyone can *read* a JWT, but only the server can
*create* a valid one. Changing `sub` to another id breaks the signature. We pin
`algorithms=["HS256"]` so a token can't choose a weaker algorithm.

### Where the token lives — httpOnly cookie
Set in [api/auth.py](../backend/app/api/auth.py) `_set_auth_cookie`:

| Flag | Effect |
|------|--------|
| `HttpOnly` | JavaScript can't read it, so an XSS bug can't steal it (localStorage *can* be read by any script on the page) |
| `Secure` (prod) | Only sent over HTTPS |
| `SameSite=Lax` | Not sent on cross-site POST/PUT/DELETE → basic CSRF protection |
| `Max-Age` 24h | Matches the JWT `exp` |

Logout deletes the cookie. Since there's no server-side session, a stolen token stays valid until
it expires. That's the trade-off of stateless JWTs (a v2 fix: token versioning or a denylist).

### Rate limiting — [core/rate_limit.py](../backend/app/core/rate_limit.py)
One small `RateLimiter` class (a *sliding window*: "at most N events per key in the last W
seconds") guards everything that is public, slow, or costs money. Over the limit → **429**.

| What | Limit | Key | Why |
|------|-------|-----|-----|
| Failed logins | 5 / 15 min | email | stops guessing one account's password |
| Failed logins | 20 / 15 min | IP | stops *password spraying*: one common password against many emails |
| Sign-ups | 5 / hour | IP | each costs a slow bcrypt hash; stops bulk fake accounts |
| Test email | 1 / 10 min, 5 / day | user | each is a real email from the Brevo quota |
| Test email | 100 / day | whole app | a ceiling no matter how many accounts someone makes |

**Why the test-email limit matters most.** Sign-up doesn't prove you own the address. Without
limits, anyone could register a stranger's email (with a phishing line as their "name") and
press "Send test email" in a loop: spam sent in *our* name, the quota gone, the Brevo account
suspended. Proper email verification is the v2 fix.

**Which IP?** Behind a proxy, `request.client.host` is the proxy, not the visitor. The usual
`X-Forwarded-For` header is *client-controlled* at its start (on Render the proxy appends to
whatever the visitor sent), so trusting it would let an attacker pick a new "IP" per request.
Render sits behind Cloudflare, which sets `True-Client-IP` and overwrites any value the visitor
sends; `CLIENT_IP_HEADER` names it ([deps.py](../backend/app/core/deps.py) `get_client_ip`).

The counters live in memory: fine for one process, but they reset on restart and each instance
would count separately. With several instances you'd move them to Redis. Memory can't grow
forever: empty keys are dropped and stale ones swept once there are 10,000.

### Request size limit — [main.py](../backend/app/main.py) `BodySizeLimitMiddleware`
Pydantic limits each field (a title is ≤ 200 characters) but only *after* the whole body has
been read and parsed. So a middleware refuses bodies over 64 KB (**413**) from the
`Content-Length` header, before anything is read. Chunked uploads have no declared length, so
they get **411** (browsers always send a length for `fetch` bodies).

### Frontend side
The browser can't read the cookie, so on load [AuthProvider.tsx](../frontend/src/auth/AuthProvider.tsx)
asks `GET /api/auth/me`: 200 = logged in, 401 = not. [RouteGuards.tsx](../frontend/src/auth/RouteGuards.tsx)
redirects accordingly. A global handler in [main.tsx](../frontend/src/main.tsx) treats *any* 401
as "logged out", which handles expired cookies.

**Logging out** ([session.ts](../frontend/src/auth/session.ts)) is order-sensitive. The server
deletes the cookie, then the app sets the cached "me" to `null` *first* (the route guard swaps the
private pages for a redirect) and only then drops the rest of the cache. An earlier version
cleared the whole cache at once, which also removed "me": the Home page, still on screen,
re-fetched its data without a cookie and showed "Not authenticated." instead of logging out.
Lesson: with a client cache, *what you remove and in which order* decides what re-renders.

**Check yourself:** Why is a token in localStorage riskier than in an httpOnly cookie? What stops
a user editing their JWT to become user 1? What does `SameSite=Lax` protect against?

---

## 7. Data isolation

The hard rule: **every todo/finance query filters by the current user.**

```python
# repositories/todo.py
stmt = select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id)
```

- The `user_id` always comes from the verified token (`CurrentUser`), **never** from the request body.
- Another user's id simply isn't found → **404**, not 403. A 403 would confirm the record exists.
- Lists, counts, stats sums, CSV export and reminders all go through methods that take `user_id`.
- Every resource has an **isolation test** (`test_isolation_between_users` in
  [test_todos.py](../backend/tests/test_todos.py), [test_finances.py](../backend/tests/test_finances.py),
  plus home and reminders): user B tries get/put/toggle/repeat/delete on user A's item and must
  get 404, and A's data must be unchanged.

**Check yourself:** If someone sends `{"user_id": 1}` in a POST body, what happens? (Hint:
`extra="forbid"` in [schemas/common.py](../backend/app/schemas/common.py).)

---

## 8. The database

### Tables — [models/](../backend/app/models/)

```
users (id PK, email UNIQUE, password_hash, name, created_at,
       monthly_budget NUMERIC(12,2)?, email_reminders bool, last_reminder_sent_on date?)
  │ 1
  │ N   ON DELETE CASCADE
todos (id PK, user_id FK, title, description?, period, priority, category,
       due_date?, completed, completed_at?, created_at, updated_at)
       INDEX (user_id, due_date)
finance_entries (id PK, user_id FK, title, description?, period, priority, category,
       kind, amount NUMERIC(12,2) CHECK > 0, entry_date, status, created_at, updated_at)
       INDEX (user_id, entry_date)
```

- **Primary key**: unique id per row. **Foreign key**: `user_id` must point to a real user.
  `ON DELETE CASCADE`: deleting a user deletes their rows (used by "Delete account").
- **Composite index `(user_id, due_date)`**: almost every query is "this user's items by date".
  The index lets Postgres jump straight to them instead of scanning the table.
- **CHECK constraints** (in the migrations): the database itself refuses `priority = 'urgent'` or
  `amount = -5`, even if a bug bypasses Pydantic. This is defence in depth.
- Enums are stored as `VARCHAR(10)` + CHECK rather than a native Postgres ENUM, because those
  are awkward to change in migrations.

### Money
`NUMERIC(12,2)` is exact decimal. Floats are binary: `0.1 + 0.2 = 0.30000000000000004`. The test
`test_stats_counts_only_paid_and_is_exact` proves `0.10 + 0.20 = "0.30"`. The chain is Postgres
`NUMERIC` → Python `Decimal` → JSON string → TypeScript string → displayed via string digits.
Only charts convert to `number`, and only to draw bar heights.

### Transactions
`db.commit()` makes changes permanent atomically: all or nothing. Tests wrap each test in a
transaction and **roll it back**, so tests never see each other's data
([conftest.py](../backend/tests/conftest.py)).

### Migrations — why Alembic, never `create_all`
`create_all` only creates *missing* tables; it can't add a column to a live table with real data.
Alembic migrations are numbered scripts with `upgrade()` and `downgrade()`, checked into git:

```
0001_create_users → 0002_create_todos → 0003_create_finance_entries → 0004_user_settings
```

`0004` shows the safe way to change a live table: new columns are nullable or have a server
default, so existing rows stay valid. Alembic records the applied version in `alembic_version`.
**Never edit an applied migration**; add a new one. CI runs `alembic check` to prove models and
migrations agree. Production runs `alembic upgrade head` on every start (see
[Dockerfile](../Dockerfile)).

**Check yourself:** What does the index `(user_id, due_date)` speed up? Why add a column as
nullable first? What does `alembic check` catch?

---

## 9. Pydantic vs SQLAlchemy vs PostgreSQL

| Concern | Pydantic (schemas/) | SQLAlchemy (models/, repositories/) | PostgreSQL |
|---------|--------------------|-------------------------------------|------------|
| Job | Validate and convert data at the **API boundary** | Map Python objects ↔ rows; build SQL | Store data durably; enforce integrity |
| Example | `amount: Decimal(gt=0, decimal_places=2)`; `extra="forbid"` | `select(Todo).where(...)`; `Numeric(12,2)` | `CHECK (amount > 0)`, FK, UNIQUE email |
| Fails with | 422 + field message | Python exception | Integrity error |
| Sees | Request/response JSON | Python objects in a Session | Rows on disk |

Three layers of checking is intentional: Pydantic gives users friendly messages, and the database
is the last line of defence.

---

## 10. API design

Interactive docs: run the app and open **http://localhost:8000/docs** (Swagger UI, generated by FastAPI).
They are switched off in production, where they would only be a map for attackers.

| Verb | Meaning here | Example | Success |
|------|--------------|---------|---------|
| GET | read | `GET /api/todos?priority=high&limit=20` | 200 |
| POST | create / action | `POST /api/todos`, `POST /api/todos/7/repeat` | 201 |
| PUT | replace the whole item | `PUT /api/todos/7` | 200 |
| PATCH | change part | `PATCH /api/auth/me`, `PATCH /api/todos/7/toggle` | 200 |
| DELETE | remove | `DELETE /api/todos/7` | 204 (no body) |

Status codes used: 200, 201, 204, 401 (not logged in), 404 (not found *or not yours*), 409 (email
taken), 422 (validation), 429 (rate limit), 503 (email provider/database down).

- **Filtering/sorting/pagination** in the query string. Lists return
  `{items, total, limit, offset}` so the UI can draw "Page 2 of 5". A tie-breaker sort on `id`
  keeps pages stable.
- **PUT vs PATCH**: the to-do form sends everything → PUT. Settings change a few fields → PATCH
  with `exclude_unset`, so omitted fields stay as they are.
- **Fixed routes before parameterised ones**: `/finances/stats` is declared before
  `/finances/{entry_id}`, or "stats" would be parsed as an id.

---

## 11. The frontend

### Structure
- **One API client** ([api/client.ts](../frontend/src/api/client.ts)): the only `fetch` in the
  app. Adds `credentials: "include"`, turns FastAPI errors into readable `ApiError`s.
- **Types mirror the backend** ([api/types.ts](../frontend/src/api/types.ts)). TypeScript `strict`
  plus eslint's `no-explicit-any` mean a typo in a field name fails the build.
- **features/** group code by feature (todos, finance); **pages/** compose features into screens.

### Server state vs UI state
- *Server state* (to-dos, stats) lives in **TanStack Query**. `useQuery({queryKey, queryFn})`
  caches by key; the key includes the filters, so each filter combination is cached separately.
  `placeholderData: keepPreviousData` keeps the old page visible while the next loads.
  After a change, `useDataMutation` ([lib/queries.ts](../frontend/src/lib/queries.ts))
  invalidates all data queries, which is simple and always correct.
- *UI state* (which tab, the form fields, the search box) lives in `useState`, or in the **URL**
  for tabs (`?tab=finance&view=stats`) so links and the back button work.

### Routing — [App.tsx](../frontend/src/App.tsx)
`PublicOnly` wraps Login/Register; `RequireAuth` wraps everything else and redirects to `/login`,
remembering where you were going.

### Details worth noticing
- **Code splitting**: the charts page is loaded with `React.lazy` ([DashboardPage.tsx](../frontend/src/pages/DashboardPage.tsx)),
  so the chart library (~110 kB gzipped) downloads only when someone opens Charts. That cut the
  first download from 722 kB to 334 kB.
- **Modal focus**: `showModal()` focuses the first button (×); [ui.tsx](../frontend/src/components/ui.tsx)
  then moves focus to the field marked `data-autofocus`, so you can type straight away. (A bug
  found by clicking through the real app, not by unit tests: a good reason to do both.)
- **Search debounce** (`useDebounced`): wait 300 ms after typing stops before calling the API.
- **Dates** ([lib/dates.ts](../frontend/src/lib/dates.ts)): `new Date("2026-03-15")` is UTC
  midnight and can display as the 14th in some time zones, so we parse the parts manually.
- **"Today"** on the server is computed in `APP_TIMEZONE` ([core/clock.py](../backend/app/core/clock.py)),
  because servers run in UTC but your "today" starts at midnight in India.
- **Theme**: CSS variables in [styles.css](../frontend/src/styles.css); dark mode only redefines
  variables. A tiny script in `index.html` sets the theme before first paint (no white flash).
  Chart colours were checked for colour-blind safety in both themes.
- **Accessibility**: priority shows colour *and* the word; native `<dialog>` for modals (focus
  trap and Esc for free); a data table under the category chart; labelled inputs; skip link.

**Check yourself:** What's in the query key for the to-do list and why? Why doesn't the frontend
store the user in localStorage?

---

## 12. Reminders: schedulers, webhooks and email

You asked about webhooks. Here's how the pieces really fit:

| Concept | What it is | Used here? |
|---------|-----------|------------|
| **Scheduler / cron** | Something that wakes up at a time and starts work | ✅ GitHub Actions `schedule` at 08:00 IST |
| **Webhook** | *Another* service calling *your* URL when an event happens there (e.g. Stripe "payment succeeded") | Only in spirit: GitHub calls our URL. Brevo can also send delivery/bounce webhooks (v2) |
| **Delivery channel** | How the message reaches the person | ✅ email (Brevo API / SMTP) |

So a reminder system is **trigger + work + delivery**:

1. **Trigger**: [.github/workflows/reminders.yml](../.github/workflows/reminders.yml) runs daily
   and `POST`s `/api/internal/reminders/run` with header `X-Cron-Secret`.
2. **Work**: `ReminderService.run_daily` ([services/reminders.py](../backend/app/services/reminders.py))
   finds opted-in users who haven't had a digest today, builds each one's list, and sends it.
3. **Delivery**: an `EmailSender` ([core/email.py](../backend/app/core/email.py)).

Design points:
- **Idempotency**: `last_reminder_sent_on` means running the job twice sends nothing new.
  Schedulers *do* retry and double-fire, so jobs must be safe to repeat. A failed send isn't
  marked, so the next run retries it.
- **Shared secret** + `secrets.compare_digest` (constant-time compare) protects the endpoint. If no
  secret is configured the route answers 404, as if it doesn't exist.
- **Strategy pattern**: `ConsoleSender`, `SmtpSender`, `BrevoSender` share one `send()` method.
  Locally, **Mailpit** catches mail at http://localhost:8025. Production uses an HTTPS API
  because many hosts block outgoing SMTP ports on free plans.
- User text in emails is **HTML-escaped** (a to-do titled `<script>` can't inject markup).

Alternatives you could choose (and when):

| Option | Good for | Cost |
|--------|----------|------|
| GitHub Actions cron → endpoint (**ours**) | Small apps, free hosting that sleeps | Free; can run minutes late |
| Host's cron job (Render Cron, Railway cron) | Same, but on your host | Usually paid |
| APScheduler inside the app | Always-on single server | Runs twice if you scale to 2 instances |
| Celery/RQ + Redis + beat | Many jobs, retries, heavy work | Extra infrastructure |
| Cloud scheduler (AWS EventBridge, GCP Cloud Scheduler) | Production systems on that cloud | Cheap, more setup |
| **Web Push** (service worker + VAPID) | Phone/desktop notifications, no app store | Free; moderate complexity |
| Telegram bot | Instant mobile messages | Free |
| SMS / WhatsApp (Twilio) | Reaching anyone | Paid per message |

---

## 13. Testing strategy

Backend: **59 pytest tests** against a **real Postgres** (not SQLite, because behaviour like
`NUMERIC`, `ILIKE` and `to_char` must match production).

- **Schema via migrations**: the session fixture runs `alembic upgrade head` on the test DB, so
  every test run also tests the migrations.
- **Rollback per test**: each test runs in a transaction that's rolled back. Fast and isolated.
- **Fixtures** ([conftest.py](../backend/tests/conftest.py)): `client` (logged in as Alice),
  `client_b` (Bob), `anon`, `make_todo`, `make_entry`, `today` (freezes the clock to 2026-03-15),
  `outbox` (fake email sender).
- **What's covered**: every endpoint; validation errors; isolation for every resource; money
  exactness; date edge cases (Jan 31 + 1 month, leap years); rate limiting; CSV injection; HTML
  escaping in emails; idempotent reminder runs; retry after failed sends.

Frontend: **Vitest** unit tests for the API client, money formatting and dates (the logic most
likely to hide bugs). `tsc` strict + eslint catch type and hook mistakes.

CI ([ci.yml](../.github/workflows/ci.yml)) runs all of it plus `alembic check` and a production
Docker build on every push.

---

## 14. Docker

- **Image**: a read-only template (OS + Python + your code). Built from a `Dockerfile`.
- **Container**: a running instance of an image. Disposable.
- **Volume**: storage that outlives containers. `pgdata` keeps your dev database across restarts.
- **Compose**: describes several containers and their network. Services reach each other by name
  (`db`, `backend`, `mailpit`).

Two Dockerfiles, two jobs:

| | `backend/Dockerfile` (dev) | `Dockerfile` (prod, repo root) |
|-|---|---|
| Code | bind-mounted, hot reload | copied in, immutable |
| Frontend | separate Vite container | built in stage 1, copied into the image |
| User | root (dev convenience) | non-root `appuser` |
| Start | `uvicorn --reload` | `alembic upgrade head && uvicorn` |

**Multi-stage build**: stage 1 (Node) runs `npm run build`; stage 2 (Python slim) copies only
`dist/`. The final image has no Node and no source TypeScript, so it's smaller and has less
attack surface. **Layer caching**: dependencies are installed before copying the code, so editing
code doesn't reinstall packages.

Useful commands:
```bash
docker compose up -d --build        # start / rebuild
docker compose logs -f backend      # follow logs
docker compose exec backend bash    # shell inside the container
docker compose down                 # stop (data kept in the volume)
docker compose down -v              # stop AND delete the dev database
```

---

## 15. Deployment and the cloud

Full steps: [DEPLOY.md](DEPLOY.md). The concepts:

- **PaaS vs IaaS**: Render is a *Platform-as-a-Service*: you give it a Dockerfile, it runs it
  with HTTPS, logs, health checks and deploys. The alternative (*IaaS*, e.g. an AWS EC2 VM) means
  you manage the OS, TLS certificates, reverse proxy and restarts yourself.
- **Managed database (Neon)**: backups, upgrades and availability are the provider's job. Your
  app only needs `DATABASE_URL`. Never run your production DB inside the app container (it
  would be wiped on every deploy).
- **Configuration via environment variables** (12-factor): the same image runs everywhere; only
  env vars differ. Secrets never live in git.
- **Same origin matters**: the cookie is `SameSite=Lax`. If the page were on `app.vercel.app`
  and the API on `api.onrender.com`, those are different *sites*, so the browser wouldn't send
  the cookie on API calls. Serving the SPA from FastAPI avoids that (and CORS). The other fix is a
  rewrite/proxy on the frontend host.
- **TLS termination**: Render's load balancer handles HTTPS and forwards plain HTTP to the
  container; `--proxy-headers` tells uvicorn to trust `X-Forwarded-Proto` so it knows the
  original request was HTTPS.
- **Health checks**: Render polls `/api/health` (which also pings the DB) and only routes traffic
  to healthy instances.
- **CI/CD**: push → CI proves it works → Render auto-deploys `main`. Rollback = redeploy the
  previous build.
- **Migrations on deploy**: `alembic upgrade head` runs before the server starts. Keep migrations
  backwards compatible so old and new code can briefly run side by side.

**Scaling later** (what would change with many users): run 2+ instances (stateless JWT makes this
easy); move the rate limiter to Redis; the reminder job is already safe to double-run; add DB
connection pooling (e.g. Neon's pooled endpoint); move email sending to a background queue.

**Doing it on AWS instead** (good to know for interviews): ECS Fargate or App Runner (container),
RDS Postgres (database), SES (email), EventBridge Scheduler (cron), Secrets Manager (secrets),
ALB + ACM (HTTPS), CloudWatch (logs).

---

## 16. Security checklist

| Threat | Mitigation | Where |
|--------|-----------|-------|
| Password database leak | bcrypt (salted, slow) | core/security.py |
| Token theft by XSS | httpOnly cookie, React escapes output | api/auth.py |
| CSRF | SameSite=Lax cookie, JSON-only API | api/auth.py |
| Seeing others' data | `user_id` filter in every query + 404 + tests | repositories/ |
| Mass assignment (`"user_id": 1` in body) | `extra="forbid"`, user id from token only | schemas/common.py |
| SQL injection | SQLAlchemy bound parameters | repositories/ |
| Brute-force login | 5 failures / 15 min per email → 429 | core/rate_limit.py |
| Password spraying | 20 failures / 15 min per IP (real IP from `True-Client-IP`) | core/rate_limit.py, core/deps.py |
| Bulk sign-ups | 5 / hour per IP | services/auth.py |
| Email spam / quota abuse | test email 1 / 10 min, 5 / day per user, 100 / day total | services/reminders.py |
| Memory exhaustion | bodies > 64 KB → 413; limiter memory bounded | main.py, core/rate_limit.py |
| User enumeration | same message + timing for bad email/password | services/auth.py |
| CSV formula injection | prefix `'` on `= + - @` cells | services/finance.py |
| HTML injection in emails | `html.escape` | services/reminders.py |
| Clickjacking / MIME sniffing | `X-Frame-Options: DENY`, `nosniff` | main.py |
| Injected scripts (XSS) | Content-Security-Policy: only our files; the inline theme script by SHA-256 hash | main.py |
| HTTPS downgrade | HSTS in production (1 year) | main.py |
| API map for attackers | `/docs` and `/openapi.json` off in production | main.py |
| Path traversal on static files | `is_relative_to(root)` | main.py |
| Secrets in git | env vars, every `.env*` ignored except the template, Render-generated JWT secret | .gitignore, render.yaml |
| Container breakout impact | non-root user | Dockerfile |

---

## 17. Design decisions and trade-offs

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| Token storage | httpOnly cookie | localStorage + Authorization header | XSS can't read it |
| Sessions | Stateless JWT, 24h | Server sessions table | No DB lookup per token; trade-off: can't revoke early |
| Deploy shape | One container (API + SPA) | Separate frontend host | Same-origin cookies, no CORS, one thing to deploy |
| DB access | Sync SQLAlchemy | Async | Simpler; thread pool is plenty at this scale |
| Enums in DB | VARCHAR + CHECK | Native ENUM | Easier migrations |
| Money in JSON | String | Number | No float rounding anywhere |
| Recurring items | "Repeat next period" button | Recurrence engine | 90% of the value, 10% of the complexity |
| Reminder trigger | GitHub Actions → secret endpoint | In-app scheduler | Free host sleeps; scheduler would sleep too and double-run when scaled |
| Email | Strategy pattern, Brevo API | Hard-coded SMTP | Swap providers by config; SMTP often blocked on PaaS |
| Server state (UI) | TanStack Query | Redux / hand-written effects | Caching and invalidation solved |
| Invalidation | Invalidate all data queries | Precise per-key updates | Simple and correct; cost is a few extra GETs |

---

## 18. How to extend it — worked example

*"Add a `notes_pinned` boolean to to-dos."*

1. **Model**: add `notes_pinned: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))` to
   [models/todo.py](../backend/app/models/todo.py).
2. **Migration**: `docker compose exec backend alembic revision --autogenerate -m "todo pinned"`, then
   **read** the generated file in `alembic/versions/` and fix anything odd. Apply with
   `alembic upgrade head`.
3. **Schemas**: add the field to `TodoWrite` and `TodoRead` ([schemas/todo.py](../backend/app/schemas/todo.py)).
4. **Repository/service**: only if there's new querying or a new rule.
5. **Tests**: add a case in `test_todos.py`; run `pytest`.
6. **Frontend**: add it to `Todo`/`TodoInput` in [types.ts](../frontend/src/api/types.ts) (the
   compiler then shows every place to update), the form and the row.
7. `alembic check`, `npm run lint`, commit, push. CI and Render handle the rest.

---

## 19. Interview questions you can now answer

1. Walk me through what happens when a user submits a form in your app. (§4)
2. Authentication vs authorization: where is each in your code? (§6, §7)
3. Why httpOnly cookies instead of localStorage? What's the CSRF story? (§6)
4. How do you guarantee users can't read each other's data, and how do you test it? (§7)
5. Why NUMERIC and not FLOAT for money? Show the test. (§8)
6. Why migrations instead of `create_all`? How do you add a column to a table with data? (§8)
7. Pydantic vs SQLAlchemy vs Postgres constraints: why validate three times? (§9)
8. PUT vs PATCH? Why 404 not 403 for others' records? (§10, §7)
9. How does your daily email job avoid sending duplicates? (§12)
10. Webhook vs cron job? (§12)
11. Why one container for frontend and backend in production? (§15)
12. What changes if you go from 1 to 10 server instances? (§15)
13. How are tests isolated from each other and from dev data? (§13)
14. What is a multi-stage Docker build and why use it? (§14)

---

## 20. Resume bullets

- Built and deployed a full-stack personal productivity and finance app (**React + TypeScript,
  FastAPI, PostgreSQL, SQLAlchemy, Docker**) with per-user data isolation, used by friends at a
  public HTTPS URL.
- Designed a layered backend (routers → services → repositories) with **JWT auth in httpOnly
  cookies**, bcrypt, login rate limiting, and **exact-decimal money handling** end to end.
- Implemented an idempotent **daily email reminder pipeline** (GitHub Actions scheduler →
  secret-protected endpoint → pluggable email providers), tested locally with Mailpit.
- Wrote **59 integration tests** against a real Postgres (migrations applied per run, transaction
  rollback per test, isolation tests for every resource); **CI/CD** with GitHub Actions and
  auto-deploy to Render with managed Postgres on Neon.
- Built analytics dashboards (monthly income vs expense, category breakdown, budget tracking)
  with Recharts and colour-blind-safe palettes; CSV export with formula-injection protection.

---

## 21. Glossary

| Term | Meaning |
|------|---------|
| ASGI | The Python interface between a server (uvicorn) and an async-capable app (FastAPI) |
| CORS | Browser rule controlling which *other* origins may call your API |
| CSRF | A malicious site making your browser send a request with your cookies |
| XSS | Attacker's script running inside your page |
| Origin / Site | Origin = scheme + host + port; Site = registrable domain (e.g. `onrender.com` subdomains differ) |
| Idempotent | Doing it twice has the same effect as once |
| ORM | Object-Relational Mapper: classes ↔ tables |
| Migration | A versioned script that changes the schema |
| Index | A lookup structure so the DB finds rows without scanning everything |
| PaaS | Platform-as-a-Service: you ship code/containers, the platform runs them |
| CI/CD | Continuous Integration (test every change) / Continuous Delivery (deploy automatically) |
| 12-factor | Conventions for cloud apps, e.g. config in environment variables |
| SPA | Single-Page Application: one HTML page, JS swaps the views |
| Debounce | Wait until input stops before acting |
