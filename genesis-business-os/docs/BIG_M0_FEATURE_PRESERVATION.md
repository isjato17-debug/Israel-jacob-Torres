# M0 feature preservation inventory

Starting commit: `95b192cefc018145c4c054db31b643aac4225428`.
This includes the previously synchronized implementation and the two directive uploads.
Inspection is of code, not a claim that every capability is operational or production-ready.
The table captures the **pre-change inspection** and its then-pending checks. Final
verification results below supersede those pending labels.

| Feature | Existing route/module | Status and dependencies | Reuse / required modification | Regression / result |
|---|---|---|---|---|
| Accounts, sessions, logout | `/api/auth/*`, `/api/me`, `security.py` | Implemented; Argon2, session DB, CSRF | Preserve existing authentication | security/auth tests; pending current pass |
| Founder profiles, Founder DNA, readiness | `/api/founder`, `/api/founder-dna`, `product_engine.founder_score` | Deterministic assessments | Preserve | founder/product tests; pending |
| Businesses and Digital Twin | `/api/businesses`, `/{bid}/twin`, `/{bid}/actuals` | Persistent, tenant-scoped simulations | Reuse Business; enforce customer ownership for new private projects | product/isolation tests; pending |
| Executive Board | `/{bid}/board`, `services/consultant.py` | Rule-based perspectives, not live AI | Preserve deterministic engine | consultant tests; pending |
| Battle Mode, Failure Lab, scenarios | `/{bid}/battle`, `/{bid}/failure-lab` | Deterministic forecasts | Preserve | product/consultant tests; pending |
| Financial calculations and strategy | `/api/consultant/generate`, `financial_model`, `generate_candidates` | Assumption-based templates | Reuse classification and financial calculations; itemize new estimates | financial/new planning tests; pending |
| Mission Control, execution plans and results | `/{bid}/command-center`, `/execution`, `/plan-vs-actual`, `/decision-ledger` | Saved tasks, forecasts versus actuals | Reuse ExecutionTask for new project next actions | product/execution tests; pending |
| Route/evolution engine | `/api/route/*`, `route_engine.py` | Portfolio, next-turn, reroute, counterfactual, evolution | Preserve | evolution tests; pending |
| Evidence and approval workflows | `/api/evidence`, `/api/decisions/*` | Evidence classes and human decisions | Preserve, no new external execution | security/execution tests; pending |
| Guided Start/Run/Grow | `/next/`, `/api/v2/journeys` | Consented saved intake, persistent resume | Preserve; add discoverable Idea Vault link | saved journey tests; pending |
| Guest planning and discovery | `/next/draft/`, `/api/v2/plan`, `/catalog` | Stateless, no filing | Preserve | v2 planning tests; pending |
| Multilingual consultations and voice | `ConsultationPanel`, guided/consultation locale modules | Six languages, Arabic RTL; browser-dependent speech | Preserve languages and speech; add localized privacy controls | consultation tests/browser; pending |
| Consultation privacy | `/journeys/{id}/consultation` | Consent on save; no revoke/delete implementation found in checkout/history | Add explicit revocation, user-confirmed transcript erasure and re-consent; retain record tombstone | new privacy tests; pending |
| Owner console, campaigns, budgets, reviews | `/next/owner/`, `v2/growth.py` | Allowlist + role + tenant checks; reversible archive and version guards | Preserve | owner growth tests; pending |
| Partner intake, histories, categories | `/next/partners/`, `v2/partners.py` | Private applications; explicit consent | Reuse category vocabulary, do not create marketplace | partner tests; pending |
| Partner review, evidence, agreements, suspension | `/next/owner/partners/` | Manual attestations, invalidation, stale-write guards; ACTIVE blocked | Preserve tenant-scoped reviewer boundaries | partner tests; pending |
| Co-marketing drafts and attribution | `v2/partner_promotions.py` | Internal-only, relationship invalidation | Preserve; no publishing/referrals | partner tests; pending |
| Government resource discovery | `official_resources.py`, `v2/catalog.py`, `partner_contracts.py` | Public references, 50 states/DC discovery; not connected APIs | Reuse official-resource classifications; preliminary requirements only | foundation/partner tests; pending |
| Payment/provider foundations | `execution_hub.py`, Square webhook, provider status | Existing adapters/configuration; live capability not established | Preserve Square and disabled payment/AI boundaries | execution/foundation tests; pending |
| Automation and budget guards | `automation_foundation.py` | Planning only, zero live spend | Preserve | foundation tests; pending |
| Community | `/api/community/*` | Posts, replies, reporting, blocking, owned deletion | Preserve | community tests; pending |
| Security, audit, throttles, readiness | middleware, security services, `/api/readyz` | CSRF, tenant isolation, lockdown, minimized audit; throttle process-local | Extend same controls; do not weaken or certify production | security/foundation tests; pending |
| Schemas, migrations, records | models; `g0001` through `g0005` | Existing migrations unchanged; additive development tables | Add new migration only; no migration against original records | migration/no-drift and read-only row comparison; pending |
| Legacy frontend and advanced navigation | `/`, static `genesis.js`, React App | Existing UI remains available | Keep routes and entry points; additive private customer surface | existing regressions + browser smoke; pending |

## Preservation evidence before editing

Read-only SQLite integrity: both databases `ok`. Root: 18 tables, zero rows.
Application: 23 tables, 154 rows. Recovery copies, exact original-row snapshots and a
Git source bundle are in excluded `generated-artifacts/m0-preservation/`.
No original records were used for QA.

## Scope

Only M0 and the first working M1 slice are authorized. No M2–M10 implementation,
credential changes, paid AI, external APIs, filings, charges, publishing or deployment.
The customer-facing M1 estimate workflow is deterministic, not genuine AI.
Requirements and provider needs are preliminary review prompts, not verified legal advice.

## Final preservation results

| Feature group from the inventory | Final regression result | Additional evidence / limit |
|---|---|---|
| Authentication, accounts, sessions, logout, CSRF | PASS: existing security suites | New UI logout/login resumes the same budget, project and task |
| Founder profiles, DNA and readiness | PASS: founder/product suites | No routes or scoring engine removed |
| Business, Digital Twin, financial scenarios | PASS: product/consultant suites | Existing financial engine reused; new private projects exclude same-tenant non-owners |
| Executive Board, Battle Mode, Failure Lab | PASS: existing consultant/product regressions | Existing advanced UI/routes preserved; not live AI |
| Mission Control, execution tasks, actuals/variance and ledger | PASS: product/execution suites | Project task persistence browser-confirmed |
| Route portfolio, next-turn, reroute, counterfactual and evolution | PASS: evolution regressions | Stateless and saved behavior retained |
| Evidence, decisions and approval gates | PASS: security/execution regressions | Additional private-project ownership checks; no external approval implied |
| Start/Run/Grow saved intake, guest plans and discovery | PASS: journey/v2 suites | Existing guided browser flow still works |
| Multilingual consultation and browser speech foundation | PASS: consultation/localization regressions | Arabic privacy RTL and Spanish new controls browser-confirmed; voice device support unchanged |
| Consultation privacy | PASS: new privacy suite, including in-flight deletion | Withdrawal, erasure, explicit re-consent and reload verified in browser |
| Owner console, campaigns, budgets, review/archive | PASS: owner growth regressions | Allowlist, role and tenant boundaries retained |
| Partner intake/review/evidence/agreement/suspension/invalidation | PASS: all partner regressions | No reviewer privilege expansion; ACTIVE still blocked |
| Promotions, permissions and attribution drafts | PASS: partner regressions | Planning-only, no ads/referrals/publishing |
| Government references, 50 states/DC and service discovery | PASS: partner/foundation/v2 regressions | Discovery/reference classification only |
| Square/payment/provider configuration and automation guards | PASS: execution/foundation regressions | Local SendGrid/Square NOT_CONFIGURED; AI/checkout disabled |
| Community posts/replies/reporting/blocking | PASS: community regressions | Existing routes unchanged |
| Security, audit, readiness and process-local rate limits | PASS: security/foundation regressions | No new production-security certification; shared limits remain unfinished |
| Original schema/migration history and customer records | PASS: SQLite/PostgreSQL migration + exact original-row comparison | All 154 rows/23 original tables unchanged; integrity and FK checks pass |
| Legacy workspace and all existing API entry points | PASS: source-preservation assertion | All 77 original API decorators and all prior migrations retained; no UI/route deletion |

Full backend pass: **142 tests**. Final affected Idea Vault pass after refinements:
**18 tests**, including additional financial/industry cases. Separate execution suite:
**3 tests**. TypeScript and final production build passed. Authenticated acceptance
passed at 390×844 and 1280px after correcting the initial plan-card overflow.

The detailed delivery report distinguishes automated regression, static preservation
and authenticated browser evidence; a passing regression is not certification that
an unfinished or simulated capability is operational.
