# Genesis production-readiness verification

Verification date: **2026-10-06, America/New_York** (some tool timestamps are 2026-10-07 UTC).

**SAFE TO DEPLOY: NO. No deployment was performed.**

> Historical preparation snapshot. The dependency findings below are the pre-remediation baseline. See [DEPENDENCY_SECURITY_REMEDIATION.md](DEPENDENCY_SECURITY_REMEDIATION.md) for the subsequent clean audit, full dependency changes and fresh regression results. Live production certification remains unavailable; no release-gate status was promoted.

## Canonical gate totals

`REAL_EXECUTION_1000_GATE_MATRIX.json`: **400 PASS / 0 FAIL / 600 RELEASE GATE**, counted from exactly 1,000 distinct gates. No gate status was promoted. Dependency release-gate evidence was updated to reflect the current scans. The conflicting historical subset remains separate.

These counts are not a clean security bill or production certification: unresolved dependency findings and the live-infrastructure checks below are release blockers.

## Scoped QA cleanup

Only the workspace created by the latest authenticated QA run was deleted transactionally: **1 tenant, 1 user, 1 business, 1 session and 3 audit rows**. Other target-related counts were zero. Complete before/after comparisons of all non-target records matched before commit. No pre-existing user, business or workspace data changed or was deleted.

The active development database retained **11 tenants** and the removed QA tenant remained absent in a subsequent read-only check. No persistent backup copy containing user data was created.

Fresh browser verification used an independent temporary SQLite database, not the active development database. The temporary database and local PostgreSQL instance were removed after verification.

## PostgreSQL migration result

On a newly initialized disposable **PostgreSQL 17.5** instance:

- `alembic upgrade head`: passed; **19 public tables**, including the revision table.
- `alembic current`: **g0001 (head)**.
- `alembic downgrade base`: passed; only the empty Alembic revision table remained.
- Second `alembic upgrade head`: passed.
- `alembic check`: **No new upgrade operations detected**.
- Production-mode local startup accepted the current migrated revision with synthetic test-only security settings.
- Missing migration revision was rejected.

The local server used an isolated loopback port and a disposable `runner` role with trust authentication. This does **not** verify production PostgreSQL credentials, TLS, availability, privileges, backups or recovery. The rollback check was against an empty disposable schema; it does not prove data-preserving rollback of a populated production database. See `PRODUCTION_DATABASE_MIGRATION_GATE.md`.

## Fail-closed and security results

Startup subprocess checks rejected:

- Missing production secret.
- SQLite in production.
- Missing production database URL.
- Insecure cookies.
- HTTP allowed origin.
- Wildcard trusted hosts.

Local regressions verified:

- Secure / HttpOnly session cookie and SameSite=Strict cookie attributes.
- Server-recorded random sessions; logout revocation, absolute expiry and idle timeout.
- CSRF missing/mismatched token rejection and matching token acceptance.
- Allowed CORS preflight and rejection of an untrusted origin.
- Rejection of an untrusted Host.
- CSP, anti-framing, no-sniff and no-store headers.
- HSTS in production-mode responses.
- Authentication rejection, owner/member authorization and cross-tenant resource rejection.
- Authentication throttling at eight failed attempts and HTTP 429 general rate limiting.
- Lockdown blocks business writes.
- Production API docs disabled.
- SendGrid email and Square payment execution points remain `NEEDS_CONNECTION`; no external provider was invoked.

Narrow fixes removed unused JWT imports/dependencies and the hardcoded development secret default. The production secret requirement remains in place. General rate limiting now returns HTTP 429 instead of raising an exception from middleware.

### Security scanners

- Dependency audit: **14 raw entries: 1 critical, 4 high, 9 moderate**.
- Static analysis: **0 findings**, scan completed.
- Privacy/data-flow scan: **0 findings**.

The raw dependency count includes repeated pytest entries and advisory aliases. It represents **9 distinct advisory groups across 7 packages** after grouping the pytest aliases/repeats.

| Package | Finding severity | Required action / exposure |
| --- | --- | --- |
| proxy-addr 2.0.7 | Critical | Fix available in 2.0.8. Pulled by Express in the retained Node API scaffold; the configured Genesis API currently runs Python, not this Express server. Do not treat the workspace finding as resolved or activate that scaffold without remediation. |
| brace-expansion 5.0.9 | Two high, one moderate | Fix all reported advisories with at least 5.0.12 through compatible dependency updates; currently pulled by API code-generation tooling. |
| braces 3.0.3 | High | No fixed version listed by the scanner; review/update or replace its fast-glob/micromatch parent chain in the mockup sandbox. |
| source-map-js 1.2.1 | High | Fix available in 1.2.2; Tailwind/Vite/PostCSS build chain. |
| fast-uri 3.1.7 | Moderate | Fix available in 3.1.8; API code-generation chain. |
| postcss-selector-parser 6.0.10 | Moderate | Fix listed in 7.1.6; Tailwind typography build dependency, requiring compatibility review. |
| pytest 8.4.2 | Moderate | Fix listed in 9.0.3; test tooling, major-version update currently outside the declared `<9` constraint. |

Build-only exposure is not equivalent to a clean supply chain. No blanket dependency overrides or major library swaps were applied. Unused python-jose and ecdsa findings disappeared after removal.

## Test results

- Complete backend suite: **39 passed**, two dependency deprecation warnings.
- Execution-layer suite: **3 passed**.
- Production frontend build: **passed**, using `PORT=5173 BASE_PATH=/ pnpm --filter @workspace/genesis-app run build`.
- Managed API restarted successfully; application startup completed and served requests.
- Existing preview screenshot: approved sign-in UI renders. Expected unauthenticated `/api/me` 401. The only UI change was a targeted Home mobile grid correction described below; no redesign.

## Authenticated browser and mobile results

One isolated Chromium browser pass verified:

1. Registration, workspace setup, three route options and persistence after reload.
2. Ask Genesis: actual `/api/consultant/generate` response, HTTP 200.
3. Business DNA: four saved inputs and derived readiness status persisted after reload.
4. Evolution: actuals requirement, saved business actuals and a returned GEN 4 comparison.
5. Community: post creation, category filtering and reply display.
6. Prepared business-plan action: `VERIFIED` from recorded evidence; external execute actions remained disabled at `NEEDS_CONNECTION`.
7. Logout and subsequent sign-in returned to the saved dashboard.

No JavaScript `pageerror` exceptions were captured. Unauthenticated transition requests produced 401s; the isolated FastAPI-served frontend also requested `/favicon.svg`, which is not mapped by that server and returned 404. The file exists in the normal Vite public directory. These did not block the authenticated flows.

The initial browser verdict was a mobile failure: Home overflowed at **402×844** while Ask, My Business, Community and Do It did not. Investigation found a desktop `grid-column:2` placement still creating an implicit second column in the mobile one-column Home grid.

A narrow CSS fix reset that card to column 1 and allowed the mobile parent tracks to shrink. A targeted real-Chromium confirmation with a signed-in disposable account and copied synthetic journey data then measured:

- **402px mobile:** document client/scroll width and body scroll width all **402px**; all Home cards inside x=12…390, one 378px column, no horizontal overflow.
- **1280px desktop:** client/scroll width both **1265px** (vertical scrollbar); two intended Home columns retained, no horizontal overflow.

The corrected signed-in Home screenshot was inspected. The production frontend build was rerun successfully after this fix. Other views' passing mobile results remain valid because their layouts were not changed.

Content-quality limitation: two differently worded Ask questions returned the same consulting scenarios. API integration passed, but adaptive/contextual intelligence is not certified by this check.

## Missing production settings and connection boundary

The checked Genesis production/security/provider keys were not configured in the production environment. Secret existence was inspected without reading secret values.

Required application settings:

- `GENESIS_ENV=production`.
- `GENESIS_DATABASE_URL`: real production PostgreSQL access using `postgresql+psycopg`, with appropriate credentials, privileges and transport protection.
- `GENESIS_JWT_SECRET`: strong independently supplied production secret, at least 32 characters; still required by the startup guard.
- `GENESIS_COOKIE_SECURE=true`.
- `GENESIS_ALLOWED_ORIGINS`: actual HTTPS origin allowlist.
- `GENESIS_ALLOWED_HOSTS`: actual production hostname allowlist, without wildcard/local hosts.

Required external provider credentials, to be supplied securely rather than pasted into chat:

- SendGrid: `GENESIS_SENDGRID_API_KEY`, `GENESIS_SENDGRID_FROM_EMAIL`.
- Square: `GENESIS_SQUARE_ACCESS_TOKEN`; payment links also require `GENESIS_SQUARE_LOCATION_ID`.

The existing `SESSION_SECRET` does not substitute for these Genesis settings. No new integration, credential or hosting account was provisioned.

The unavailable boundary is the actual production PostgreSQL and hosting/domain configuration. Needed next: access to the chosen production hosting target, its HTTPS domain/TLS setup and trusted proxy settings, production database connection and verified backup/restore process, and the application security settings above. If that target requires an external hosting account, its account access must be supplied; no particular external platform is assumed or substituted.

## Remaining release blockers

1. Unresolved dependency vulnerabilities.
2. Actual production database and HTTPS hosting/security configuration unavailable.
3. Live cookie/domain/proxy behavior, credential validation and production migration/backup/restore unverified.
4. Rate limiting is process-local; multi-worker/shared enforcement and proxy-aware client IP behavior need production-like validation.
5. Additional session hardening, accessibility, concurrency/load, penetration testing, privacy lifecycle, AI injection and disaster recovery gates remain open.
6. Live SendGrid/Square behavior, webhooks and ambiguous-outcome reconciliation need credentials and provider evidence before enabled-provider certification.

Local success is not production verification. Stop at this boundary; do not publish.
