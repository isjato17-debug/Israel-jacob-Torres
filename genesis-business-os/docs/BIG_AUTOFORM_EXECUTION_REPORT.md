# B.I.G. connected consulting-to-document delivery

## Source-control and inspected baseline

- Development branch: `genesis-os-2-development`, unchanged.
- Starting commit: `46fbbc06b9a4e2ec8d316a2ed8b551957013fb97`.
- Protected `main`, Git credentials and remote history were not changed.
- The ending commit is supplied in final delivery after this report is committed.
- No deployment, paid service, payment, real signature, government filing, funding
  submission or private-document external transmission was performed.

Inspection of application code, registered routes and the actual development schema
found the existing Idea Vault, three-plan engine, private Business Projects and Mission
Control; Founder DNA, Digital Twin and Executive Board engines were present. No native
AutoForm document lifecycle or Business Passport table existed. The saved consultation
provider remained a labeled rule-based simulation, not genuine connected AI.
Existing government resources were discovery links, not filing integrations.
Existing Partner Network was private/manual, not an activated provider execution network.

All **89 pre-existing route decorators** are retained, and `g0001`–`g0006` are unchanged.
The design, legacy workspace, existing consultation languages/privacy and advanced
features were not replaced. The new continuation lives inside the existing project's
detail screen; there is no replacement dashboard or second chatbot.

## Actual new features

1. **Connected project continuation.** Read the authorized selected project, $3,000
   budget and saved plan. Reuse the actual existing financial model, Digital Twin,
   Executive Board and customer-scoped saved Founder DNA. If no profile exists,
   explicitly show that no Founder DNA assessment was supplied; do not invent one.
2. **Minimal Business Passport.** Customer-authorized business name, representative,
   optional business contact email and municipality, scoped to the project/customer.
   This is unverified reusable business contact data, not verified identity or a
   complete identity-document vault.
3. **Reusable AutoForm foundation.** Server-owned versioned field definitions,
   strict validation, partial drafts, missing-field detection, typed integer-cent
   price, immutable generated revisions, safe rendering, private downloads,
   revision-specific approval, workflow statuses and minimized audit.
4. **A genuine document:** **Cleaning Service Agreement**, English, printable HTML.
   It includes actual entered parties, property, scope/exclusions, schedule, price,
   payment terms, supplies/access/safety, cancellation, review/change terms and
   blank provider/client signature blocks. It is not a government form or legal
   certification; appropriate professional review is disclosed.
5. **Corrections and review.** Save corrections and regenerate a new revision.
   Earlier document hashes/downloads and historical approvals remain intact.
   Corrections invalidate current readiness; approving an old version is blocked.
6. **Explicit approval and continuation.** Customer approval binds to the current
   document ID and byte hash. READY_FOR_SIGNATURE does not mean signed, executed
   or submitted. The existing project stage and a Mission Control review task
   update; the next action explains the separate appropriate signature process.
7. **Persistent private document storage.** Structured document source and version
   are stored under existing account ownership. File bytes are deterministically
   rendered on demand, not placed in database blobs, public files or an external
   bucket. Reload/logout/login do not discard source, revision or approval.
8. **External-service readiness.** A real read-only Federal Register public-data
   adapter uses a fixed generic cleaning query, no credentials and no customer
   fields. Explicit customer check reports verified public-read results or a
   clear unavailable status. Public notices are not determinations of applicability
   or a government submission connection.
9. **Paid services on standby.** Readiness view records actual prerequisites for
   DirectSubmit, signatures, professional handoff, live AI, email and existing
   payment foundations. It does not pretend these adapters are all built/connected.
   No paid provider or owner account connection was silently activated.

## Customer demonstration

The customer opens the existing cleaning-business project with the selected plan
and unchanged $3,000 budget → reviews B.I.G.'s deterministic next-supported-action
guidance → explicitly authorizes reusable Passport contact details → starts the
Cleaning Service Agreement → sees reused fields and supplies missing client/service
information → saves even a partial draft → generates the actual document → reviews
and downloads it → corrects a price and generates a new revision → explicitly approves
the exact document → sees signature preparation as the next action, with the
existing project/task updated → logs out/in and reopens the same saved workflow.

Only cleaning-service agreements are supported in this first native template.
The framework is extensible; government forms, permits, grants, loans, tax documents,
renewals and professional submissions are not falsely advertised as implemented.

## Database changes

Additive `g0007_project_autoform.py` adds four models/tables:
`BusinessPassport` / `business_passports`,
`DocumentWorkflow` / `document_workflows`,
`GeneratedDocument` / `generated_documents`,
`DocumentApproval` / `document_approvals`.

Existing Business Projects and Execution Tasks are reused and updated only through
their customer's authorized workflow actions. New-template downgrade refuses to
remove populated tables. Previous migrations are untouched.

Before editing: root SQLite had 18 tables/0 rows; application SQLite had 27 tables/154
rows. Both passed integrity and foreign-key checks. Exact row snapshots, SQLite backups
and a Git bundle were retained under excluded
`generated-artifacts/autoform-preservation/`. Browser QA uses a separate database.

## Automated verification

- Full backend regression suite: **162 passed**, including SQLite and disposable
  PostgreSQL additive migration/no-drift checks; no skipped PostgreSQL test in this run.
- Existing execution-layer suite: **3 passed**.
- Frontend TypeScript: passed.
- Production build: passed with the existing workflow PORT/base configuration.
- Additional strengthened migration preservation: **2 passed** on SQLite/PostgreSQL,
  including seeded existing private idea/revision/project/privacy rows in `g0006`
  before upgrading to `g0007`.
- New document tests prove project loading, authorized reuse, missing fields, partial
  save, generation, exact downloaded hash, corrections, immutable older downloads,
  explicit approval, next-task/stage updates, logout/login persistence, strict input,
  CSRF, lockdown, stale-write rejection, and cross-tenant AND same-tenant customer isolation.
- Security tests also verify escaped HTML input, tampering blocking, minimized audit,
  unsupported-template errors, duplicate-start reuse, and an unavailable public
  provider never being labeled connected.

An initial isolation test correctly received 401 when its fixture changed a user's
tenant without updating its session. The fixture was corrected to exercise an
authenticated same-tenant non-owner; the product's session protection was not weakened.
Pre-existing nonblocking warnings remain Starlette/httpx, Argon2 version lookup and
Alembic's path-separator default.

Authenticated acceptance passed for the exact $3,000 New York cleaning project,
Build Strong selection and retained $3,420 planning gap, consented Passport reuse,
partial and complete drafts, actual downloads, correction from $220.25 to $225.75,
revision history, explicit approval, next task/stage and logout/login persistence.
Another customer's execution/download requests returned 404; signed-out requests
returned 401. The in-app Federal Register check returned PUBLIC_READ_VERIFIED
with three public notices, while paid/consequential services remained inactive.

The first browser pass found 30px mobile overflow from long unbroken service-status
tokens. Wrapping and zero-minimum grid tracks corrected it. A focused visual-only
continuation confirmed matching client/scroll widths: 375/375 at a 390px viewport,
345/345 at 360px, and 1265/1265 at 1280px. Functional flows were not needlessly repeated.
This is viewport/browser automation, not a native iPhone/Safari or real-user usability study.

Final read-only comparison confirmed **all 154 original application rows unchanged
across all 27 original tables**; root database's 18 tables remain empty. Both databases
passed integrity checks and had zero foreign-key violations. Four new application
tables are empty in normal development; all writes for acceptance remained isolated.
The disposable browser database was removed, the disposable PostgreSQL database
dropped and its temporary service stopped. The normal database configuration and
exact starting `.replit` were restored. Both managed application workflows restarted
cleanly; API readiness returned HTTP 200 with database/schema true.

Last read-only verified GitHub development ref:
`9a81e39e2314365a02d22369946314b3c32bd4f4`. No push was attempted.
Protected main stayed at `7a09fa54d0a18dad7f5b6cca184d8258f7c47418`.

## Remaining boundaries and next dependency

- Live generative AI is **not activated**. The existing consultant engines provide
  deterministic context/guidance, explicitly labeled as such. Owner pricing/budget
  approval and a configured tested AI provider are still needed for genuine AI.
- Approval is **not an e-signature**. No biometric images or templates are stored.
  Signing needs the separately approved method/provider and required evidence.
- No external account was attached solely because a connector exists. Previously
  authorized email-account availability does not establish a no-cost entitlement,
  verified sender, or consent to transmit a customer's agreement.
- No production migration or deployment was attempted. Production durability,
  reviewed retention/backup recovery and any file-storage provider require separate
  operational review; private structured sources currently follow the existing DB.
- English agreement text needs legal review for the actual business, customer,
  municipality and situation. Wider templates/localization remain unfinished.
- First live government submission depends on choosing an exact agency/form and
  verifying its accepted submission channel/provider, sandbox/access authorization,
  required signatures, fees and status evidence. The current agreement is not a
  government form; a public Federal Register feed cannot submit one.

## Exact source files

Backend: `app/models.py`, `app/main.py`, `app/services/readiness.py`,
`app/services/document_engine.py`, `app/services/external_readiness.py`,
`app/v2/documents.py`, `migrations/versions/g0007_project_autoform.py`,
`tests/test_autoform.py`, `tests/test_big_migration.py`.

Frontend under `artifacts/genesis-app/src/v2`: `IdeaVault.tsx`,
`ProjectExecution.tsx`, `ServiceStandby.tsx`, `documents-api.ts`, `execution.css`.

Standing instructions and provenance: `replit.md`, updated project-scope/integrity
memory, this report and the untouched uploaded direct execution order.
The final commit's exact file list is authoritative.
