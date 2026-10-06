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
