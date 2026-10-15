# B.I.G. — Phase 2 implementation and authorization boundaries

## Identity and preservation

The permanent customer-facing product is **B.I.G. — Business Inside Genesis**,
**Powered by Genesis OS 2.0**. Brand message: **Think B.I.G. Build B.I.G. Become B.I.G.**
This is the existing product, not a replacement app or repository. No new logo is approved.
Repository, development branch, routes, database identifiers and existing API identifiers
are retained. Protected `main` is not a development target. Do not repeat branch renaming.

Pre-change local recovery snapshot: `generated-artifacts/backups/20261015T162349Z/`.
It contains committed source history and integrity-checked SQLite copies; it is not
off-site recovery or production PostgreSQL backup. Generated output is excluded from Git.

## Implemented customer-intelligence slice

- Mission Control loads an account- and tenant-scoped consultation for a prepared saved intake.
- Separate per-send consent is required to save the current question and simulated response.
- GET resumes saved turns; POST accepts only the current message, consent and optimistic
  consultation/intake versions. It never trusts browser transcripts or provider selections.
- Eight total turns per journey; message limit 1,200 characters; generated output has strict
  structured validation. Source IDs must come from the server-curated official-resource registry.
- English, Spanish, Mandarin Chinese, Arabic, Hindi and Swahili, plus simple/detailed
  context, come from saved preferences. Arabic uses right-to-left customer layouts.
  The original workspace and private owner console are not six-language surfaces;
  links disclose the destination language. The preliminary server checklist remains
  English with a notice in every other supported language. Translated guidance is
  not a statement of formation coverage outside the United States.
- The simulation personalizes limited stage/goal context using explicit rules. It **does not
  reason about a free-form question** and is not genuine conversational AI. This limitation
  is disclosed in each response. Its purpose is offline integration/failure/persistence testing.
- Output separates simulation, user-provided facts, unverified assumptions, professional review
  requirements and reference-only government links. No official business status is verified.
- User questions/responses live in private application records, not audit detail text.
  Audit events contain consent, turn count, mode and zero charge only.
- Authentication, CSRF, tenant/user isolation, lockdown and stale-write controls remain active.
- Existing `g0001 → g0002 → g0003` remain unchanged. Additive `g0004` introduces consultation
  records; no document bytes or financial transactions are stored. Production upgrades require
  a reviewed explicit migration. The new downgrade refuses to drop populated consultations.

## Live AI remains blocked

The server retains an OpenAI-compatible offline request builder and a typed provider boundary.
Both public analysis and reserved transport refuse live usage, even if credentials or
environment flags are present. There is no frontend live toggle or automatic paid fallback.
The available provider is explicitly `SIMULATION`; mock-provider fault tests require no network.

Before any future live activation:

1. Obtain explicit owner approval of provider, model, price, hard monthly/daily ceilings and
   permitted data sharing/retention. Do not treat a 5% planning allocation as spend authorization.
2. Add an atomic shared reservation ledger before dispatch. Reserve worst-case token cost in
   integer minor units, enforce user/tenant/agent/global ceilings and concurrency, reconcile actual
   usage, and retain reservations on ambiguous timeouts until reconciled.
3. Bound input/output tokens and timeout; forbid automatic fallback/retry that can double charge.
   Apply an allowlisted server URL, reviewed TLS/network policy and redacted error handling.
4. Add an independently labeled live-output schema; validate citations/provenance against retrieved
   authoritative sources. Treat user/model text as data, never as tool permissions.
5. Review privacy, retention/deletion, prompt injection, professional-advice escalation and
   accessibility. Isolate test credentials and obtain approval before the first billable request.

No API credits, subscription, billing activation or live AI request is authorized by this work.

## Provider-status correction

External adapters distinguish `NOT_CONFIGURED`, `CONFIGURED`, `VERIFICATION_PENDING`,
`VERIFIED_CONNECTED`, `UNAVAILABLE`, `ERROR`. Configuration alone never verifies a connection.
Only a successful actual provider response creates short-lived evidence for that capability.
Square additionally requires the expected provider-object reference. Verification expires after
five minutes, on credential changes, or process restart. Error/unavailable outcomes invalidate it.
This phase does not initiate a provider probe or external operation.

`READY` is retained for internal preparation/guide capabilities, not an external connection.
An additive `legacy_state` compatibility field reports `CONNECTED` only with verified evidence.
Existing explicitly approved execution can attempt a configured adapter; approval, risk, audit,
dispatch and reconciliation protections are unchanged. Verification of one capability does not
certify all Square capabilities or production integration readiness.

## Liveness, readiness and production throttling

- `/healthz` remains backward-compatible basic process liveness; it is not dependency readiness.
- `/api/readyz` returns generic database/schema booleans and HTTP 200/503. Development checks the
  required tables; production also compares the actual Alembic revision to the single code head.
  No database URL, provider key, driver exception or credential presence is returned.
- Disabled AI/payment providers are not active dependencies and do not block process readiness.
  A ready process is not a release approval or production-readiness certification.

### Shared rate-limiting design — planned, not implemented

The current request and failed-login counters are process-local. They reset on restart, diverge
across workers, and do not constitute a global production limit. Their per-key storage also
needs bounded expiry/eviction. A trusted-proxy policy is required to avoid grouping all customers
under a proxy IP or trusting spoofable forwarded headers.

Preferred first implementation: reuse the approved production PostgreSQL rather than buying a
cache service. Add a dedicated counter/reservation table through an additive reviewed migration:

- Key = HMAC of normalized scope/identity plus policy/window; never store raw email/IP as a key.
  Use a dedicated server secret managed through the normal secrets flow.
- Separate login identity/IP, unauthenticated requests, authenticated user/tenant, consultation
  and future agent/provider scopes. Normalize identities server-side.
- Atomic `INSERT … ON CONFLICT … DO UPDATE … WHERE count < limit RETURNING` under PostgreSQL
  database time, with bounded windows. Check all required scopes in a transaction; no
  read-then-write race. Use separate short-lived transactions, not the caller's business transaction.
- `429` and bounded `Retry-After` for exhausted limits. If shared enforcement is unavailable,
  fail closed with generic `503` for authentication/paid/external paths, not in-memory fallback.
  Keep minimal liveness exempt; rate-limit readiness separately at the trusted edge.
- Schedule bounded deletion of expired windows and cap identity cardinality. Use short connection/
  statement timeouts; measure contention. Redis is optional only if approved capacity needs it.
- Validate concurrent multi-worker limits, time boundaries, spoofed headers, outage behavior and
  pruning before configuring multiple production replicas.

This design needs implementation and verification before multi-instance deployment.

## Automation architecture — planning only

Nine named policies cover Commander, Marketing, Growth, Finance, Compliance, Intellectual
Property, Operations, Customer Support and Security. They are `PLANNED_NOT_ACTIVE`.
Only consented-context reading and draft preparation are permitted; live cents are zero.
No queue worker, scheduled task, social post, email, filing or financial action is activated.

Pure event-transition contracts distinguish draft, awaiting review, approved **plan**, blocked
and cancelled. Owner review is required for plan approval. Failure recovery returns to draft;
approval never grants external execution. Future durable coordination needs an outbox/inbox,
idempotent consumer acknowledgments, typed task dependencies, consent snapshots, tenant scope,
audited permission checks and per-agent atomic budget reservations. Persist tasks/events only
when a supported customer workflow and its failure semantics have been approved.

Revenue-budget calculation accepts server-verified collected-revenue evidence, subtracts
refunds, processing fees and restricted liabilities, floors at zero, and computes at most 500
basis points (5%) using integer cents. Unverified/projected revenue yields zero. The result is a
planning limit only; authorized spend and per-agent live limits stay zero. There is no new
payment integration, revenue mutation or owner spending toggle. A complete revenue ledger,
owner-reviewed allocations, alerts and usage reconciliation remain future work.

## Official-resource and OnePay boundaries

The resource registry distinguishes authoritative navigation links from API/status verification.
IRS, SBA, USPTO, FinCEN and Copyright Office references are provided, with no assertion that their
requirements apply to a particular business. State registration/licensing, local agencies and
other federal authorities are explicit future adapter boundaries, not claimed coverage.
Current jurisdictional obligations must be checked against current official sources before
making a recommendation. No FinCEN applicability determination or filing is automated.

SBA is included through current official business guidance, local assistance (including
SBDC/SCORE resource partners), counseling/training, loan information and licensing references.
These are links to SBA resources, not an SBA partnership, loan approval, automatic application
or verified API connection. Eligibility and any counseling/loan costs remain with the official
program/provider; B.I.G. does not promise free services or funding. Link descriptions are
localized; external government pages may use a different language.

SBA pages checked on 2026-10-15:
- https://www.sba.gov/counseling/
- https://www.sba.gov/counseling/local-assistance/
- https://www.sba.gov/loans/

The older `/business-guide`, `/local-assistance`, and `/funding-programs` URLs redirected
to SBA's reorganized counseling/loans pages. Current curated links use those destinations.

OnePay proposal remains in `GENESIS_ONEPAY_ARCHITECTURE.md`: Stripe Connect is the preferred
future candidate; Square code/history remain. Checkout, charges and payouts remain disabled.

## Verification and release status

Actual test results and exact changed files are recorded in the completion report.
The canonical baseline remains **400 PASS / 0 FAIL / 600 RELEASE GATE**; these counts are not
a percentage of feature completion and are not advanced by this development slice.

Still awaiting approval: live model/provider use, billable storage, external automation,
payments/payouts, government submissions, production credentials/infrastructure and publishing.
Still required: genuine live consultation, shared throttle implementation, a secure document
vault, verified provider/jurisdiction coverage, full durable orchestration and real-user
accessibility/usability studies. This phase does not claim production readiness.
