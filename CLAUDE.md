# CLAUDE.md — Duely

A public todo + finance web app. Learning and portfolio project: the owner studies the
architecture from `docs/GUIDE.md` rather than typing the code.

## Read first
- `docs/SPEC.md` — **what** is built. Source of truth.
- `docs/PLAN.md` — the phases and their done criteria (all built; use it for future phases).
- `docs/GUIDE.md` — the study guide. Keep it in sync when behaviour changes.
- `docs/DEPLOY.md` — how production is set up.

## Hard rules
- **Data isolation.** Every database query for todos or finances filters by the current user.
- **Money.** NUMERIC/Decimal for money. Never float. JSON carries money as strings.
- **Schema changes.** Only through Alembic migrations. Never `create_all`. Never edit a migration that has already been applied; add a new one.
- **Secrets.** Only from environment variables. Never commit `.env`.
- **Tokens.** The JWT lives in an httpOnly cookie, never in localStorage.

## Backend structure (layered, sync SQLAlchemy)
```
app/api/            routers: HTTP only (status codes, cookies, query params)
app/services/       business rules; raise domain errors from app/core/errors.py
app/repositories/   all database queries; the only layer that touches the Session
app/models/         SQLAlchemy models
app/schemas/        Pydantic request and response models
app/core/           settings, db, security, deps, email senders, clock, errors
app/scripts/        one-off commands (demo seed)
```
Routers call services. Services call repositories. Services never raise HTTPException.

## Conventions
- SQLAlchemy 2.0 typed style, Pydantic v2, sync everywhere.
- "Today" always comes from `app.core.clock.today()` (time-zone aware, patchable in tests).
- Tests: pytest against the test Postgres, one file per router, an isolation test per resource.
- Frontend: TypeScript strict, no `any`, one API client in `src/api/`, `credentials: "include"`.
- Formatting: ruff + black (Python), eslint + prettier (TypeScript).

## Commands
```
docker compose up -d --build                      # start everything
docker compose exec backend alembic upgrade head  # migrate
docker compose exec backend pytest                # backend tests
docker compose exec backend alembic check         # models match migrations?
docker compose exec backend python -m app.scripts.seed_demo   # demo data
cd frontend && npm test && npm run lint && npm run build
```

## Interaction rules
- **Scope check:** when a new feature is proposed, say whether it fits the current spec or is v2, then proceed.
- **Errors:** likely cause in one line, fix it, then explain the concept in 2–3 lines.
- **Drill mode:** on "drill <topic>", ask 5 questions one at a time from the real code, mark each
  right / partly / wrong with file:line, score out of 5. Never edit code during a drill.
