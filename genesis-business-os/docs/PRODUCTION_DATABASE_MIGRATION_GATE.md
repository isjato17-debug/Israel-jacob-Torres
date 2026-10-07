# Production Database Migration Gate
`Base.metadata.create_all()` is retained only for the reference/development build. Production release must use reviewed Alembic migrations against PostgreSQL. Deployment must run migrations as an explicit release step, support rollback/restore planning, and never silently mutate production schema at application startup. A migration is required for the Community moderation/report/block fields added by the 100-gate audit.

## Verified local release procedure

The current reviewed initial migration includes the Community fields. The fresh disposable PostgreSQL 17.5 check on 2026-10-06 completed `upgrade head` → `downgrade base` → `upgrade head`, followed by `alembic check` with no drift. The resulting revision was `g0001`.

Before a real release:

1. Supply the production PostgreSQL connection using `GENESIS_DATABASE_URL` with the `postgresql+psycopg` driver. Supply the production security settings listed in `PRODUCTION_READINESS_VERIFICATION.md`.
2. Verify a database backup and a restore on a separate database. This was not tested against production.
3. From `genesis-business-os/backend`, with production environment settings already supplied securely, run `python -m alembic upgrade head` as an explicit release step, then `python -m alembic current` and `python -m alembic check`.
4. Start the existing FastAPI application with `GENESIS_ENV=production`. Startup refuses a missing/outdated revision and never invokes development `create_all` in production.
5. Verify HTTPS, cookies, trusted proxy behavior, HSTS, readiness and authenticated flows at the actual production domain before admitting users.

**Do not run `downgrade base` on a populated production database.** The initial migration rollback drops application tables; the disposable check proves schema reversibility, not retention of business data. A production rollback must use a reviewed data-preserving plan or a verified restore.

No production database was migrated, and no hosting target was substituted or published during preparation.
