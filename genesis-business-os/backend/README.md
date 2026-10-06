# Genesis Business OS Secure MVP

A runnable foundation for the Genesis Business OS business operating system.

## Included
- Tenant-isolated accounts and backend authorization
- Argon2 password hashing and short-lived JWTs
- Founder DNA records
- Version-ready Business Twin records
- Typed Evidence Ledger
- Executive Decision Board scaffold
- Risk-tiered Authorization Gateway
- Tier-4 non-autonomous safety rule
- Tenant Lockdown Mode
- Audit trail
- Security headers, host checks, CORS restrictions, rate limiting
- Non-root/read-only container hardening
- Security CI: tests, Bandit, pip-audit

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# replace GENESIS_JWT_SECRET with a random 32+ byte secret
uvicorn app.main:app --reload
```
Open http://localhost:8000

## Test
```bash
pytest -q
```

## Important
This is a secure-by-design MVP foundation, not a claim that the application is unhackable or ready for sensitive production data. See SECURITY.md for the mandatory production-hardening gate.


## v2 Consultant Engine
Business generation, deterministic finance, CEO/CFO/CMO/COO/Risk/Cyber board, stress tests, actual-result ingestion, decision provenance, and secure command-center endpoints are included. Model providers must remain server-side and behind the Authorization Gateway.

## Production hardening added
- Production startup fails closed if the development signing secret or SQLite is used.
- PostgreSQL production compose configuration.
- Server-side, provider-neutral AI adapter; keys stay in environment secrets.
- Credential-stuffing throttling hook and generic login failure response.
- Trusted-host allowlist, no-store responses, HSTS in production.
- GitHub CI: tests, Bandit and pip-audit.
- Production security gate and Replit deployment instructions.

### Important authentication gate
The development UI still uses a bearer token for local testing. Before accepting real customer data, replace browser localStorage token persistence with a hardened identity/session provider using phishing-resistant passkeys/MFA and HttpOnly/Secure/SameSite session cookies. This is intentionally listed as a launch blocker rather than represented as complete.

## Database migrations

Alembic owns schema changes. Production startup refuses SQLite, incomplete security settings, and a database that is not at the current Alembic revision; it never creates or upgrades production tables automatically.

From `genesis-business-os/backend`, set `GENESIS_ENV=development` for local work. A new local database can be created with:

```bash
python -m alembic upgrade head
```

The development app can still create missing tables for local use. If an existing local database was created before Alembic and already has the baseline schema, compare its schema with the baseline first, then record the baseline once with `python -m alembic stamp g0001`. Do not stamp a database with an incomplete or different schema.

For production, first provision PostgreSQL and configure `GENESIS_DATABASE_URL`, `GENESIS_JWT_SECRET`, `GENESIS_COOKIE_SECURE=true`, exact HTTPS `GENESIS_ALLOWED_ORIGINS`, and exact `GENESIS_ALLOWED_HOSTS` through the environment/secrets manager. Back up the database and verify the backup before any schema change. During an explicitly approved release, run `GENESIS_ENV=production python -m alembic upgrade head`, verify `python -m alembic current`, then start the application. The application will refuse startup until the database revision matches the code.

Rollback commands are `GENESIS_ENV=production python -m alembic downgrade -1` (one revision) or `python -m alembic downgrade <revision>` (a reviewed target). Test the exact rollback and re-upgrade on a disposable PostgreSQL copy first, and retain a verified backup. The initial baseline downgrade removes the Genesis tables and all rows in them; it is only appropriate for an empty/disposable database. Never downgrade a populated production database to the baseline. Each future revision must include a reviewed downgrade that preserves or intentionally migrates data.

Backend tests force a temporary SQLite database under the system temp directory and remove it after the test session. They do not use the tracked development database or any configured production database URL.
