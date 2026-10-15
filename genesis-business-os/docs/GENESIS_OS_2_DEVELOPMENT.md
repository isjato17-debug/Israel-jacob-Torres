# Genesis OS 2.0 — reconstruction blueprint and development status

## Scope and safety

The master directive authorizes reconstruction of the existing product, not a second
project or repository. Start, Run and Grow are the primary customer journeys.
The supported initial journey is account creation/sign-in, consented one-question intake,
saved progress and a prepared launch checklist. This is not the completed ecosystem.
No paid services, government filings or publication have been authorized or performed.

The existing interface, accounts, business records, community, execution workflows,
tenant boundaries, CSRF/session controls, approvals and audit system remain in place.
The existing HTML, JavaScript and CSS frontend files are unchanged.

- Stable `main` baseline: `7a09fa54d0a18dad7f5b6cca184d8258f7c47418`.
- Reconstruction branch: `genesis-os-2-development`.
- Existing application: `/`.
- Guided development experience in the same application: `/next/`.
- Preserved original guest draft/service discovery: `/next/draft/`.
- Latest pre-change local recovery snapshot: `generated-artifacts/backups/20261015T015232Z/`.
- Snapshot includes complete committed Git history and integrity-checked copies of
  the root and backend SQLite databases. Source bundle verification succeeded.
- This is a local recovery copy, not an off-site or production PostgreSQL backup.
  External secrets are not included. Recovery instructions are beside the manifest.
- Snapshot output is excluded from Git and publishing.

## Authentication diagnosis

The agent has no visible GitHub CLI login file in its active configuration directory
or the normal home directory. No CLI authentication token is present in its environment.
Only presence metadata was inspected; credential-file contents were not read.
An account-level GitHub connection is not proof of usable CLI write credentials.
Different Shell/agent authentication contexts remain a possibility, not a proven cause.

Use one supported GitHub CLI device flow with an explicit configuration directory in
this workspace, then run `gh auth setup-git`. Browser approval must finish while that
CLI process remains alive. Never request passwords or access tokens in chat.
After authorization, inspect permissions and remote history again before pushing.
Do not force-push, reset, delete branches or create another repository.
The previous device sign-in expired without completed authorization. Never reuse an
expired code; the user must receive a new code from a currently waiting CLI process.

## Preserved architecture

- **Current frontend:** existing HTML/JavaScript under `frontend/`, served by Vite.
- **Preview:** React/TypeScript components in the existing web artifact, with a
  separate Vite HTML entry. Production output retains both HTML entries.
- **Backend:** existing FastAPI application and SQLAlchemy models, not a database
  replacement or a new authentication stack.
- **Persistence:** existing tenant/business records remain authoritative. The new
  account-bound journey table is additive; guest draft planning remains stateless.
- **Existing provider adapters:** SendGrid and Square execution remains approval-
  and evidence-oriented. No provider is certified operational by this milestone.

## Completed development

- Start / Run / Grow mobile-first discovery and intake interface.
- Search/filter across 17 business service categories.
- Planning intake for all 50 states, with legal entity and ownership structure
  represented separately. Holding companies/subsidiaries are ownership descriptions,
  not additional legal entity types.
- Real `GET /api/v2/catalog` and `POST /api/v2/plan` endpoints.
- Preliminary stage-based checklists and an explicit unsaved text download.
- Validation, errors, loading states, professional-review flags and official guidance.
- Existing session sign-in/registration integrated into the new guided experience.
- Explicit consent before saving business details. Four questions, one at a time.
- Each confirmed answer saves automatically; navigation advances only after server
  acknowledgment. Reload resumes progress. Typing alone does not confirm an answer.
- Account- and tenant-scoped progress, optimistic version protection, CSRF, lockdown
  enforcement and audit events without duplicating free-text answers in audit details.
- User-provided business facts reused across stages; the new stage asks for its own goal.
- English/Spanish interface and saved simple/detailed preferences. Preliminary
  checklist content remains English, with an explicit notice in Spanish mode.
- Initial Mission Control: saved intake, real progress, review checklist, unquoted
  costs, no authorized charges, next steps and a saved-plan text download.
- Browser-dependent optional voice dictation with explicit online-processing opt-in,
  user-triggered microphone permission and text fallback. Question read-aloud uses
  matching on-device voices only. No speech provider or paid AI service was activated.
- Additive `g0002` migration after the preserved `g0001` baseline. Existing development
  startup manages local SQLite schema; production still requires reviewed explicit
  migrations, never an automatic upgrade of a populated production database.
- No external execution, checkout, connected AI calls or government submissions.

**Important:** State selection is not state-specific formation coverage. The checklist
is selected by business stage; it is not tailored legal advice or AI-generated advice.
The user's goal is shown as context, not used to imply intelligent personalization.
No service is shown as connected merely because an adapter or credential field exists.
Journey status `PREPARED` means a preliminary plan exists. Every listed service is
`NOT_STARTED`. The new API does not accept customer-written submission/completion
statuses. Future `SUBMITTED`, `PENDING`, `APPROVED` and `COMPLETED` transitions require
provider acknowledgments or appropriate professional evidence, not a progress checkbox.

## Seven-system reconstruction blueprint

| System | Reusable foundation / implemented slice | Remaining work |
| --- | --- | --- |
| Mission Control | Existing accounts, businesses, audit/approval/execution records; new saved journey and truthful cost/progress view | Unified service orders, deadlines, provider receipts, owner reporting and alerts |
| Adaptive Intelligence | Saved language/detail preferences, progressive intake, optional browser speech | Authorized model, conversational reasoning, grounded personalization and accessibility research with real users |
| Business Autopilot | Existing risk tiers, explicit approvals and SendGrid/Square execution adapters | Durable task orchestration, provider contracts, consent scopes, idempotent submissions/webhooks and reconciliation |
| First Customer Engine | Existing business/route context | Consent-aware lead/opportunity records, outreach planning, connected channels and actual opportunity/sales evidence |
| Business Health Monitor | Existing business records and security controls | Verified jurisdictional obligations, sourced deadlines, finance feeds, scheduled checks and explainable risk alerts |
| Business Passport | Consented reuse of the same user's self-reported intake | Private document vault; field-level sharing permissions; provenance, verification, expiry and revocation |
| Expansion Architect | Existing multiple-business records; distinct legal-entity/ownership choices | Parent/subsidiary/brand relationships, ownership interests, permissions and professionally reviewed expansion plans |

Self-reported information is never labelled verified. A holding company is an
ownership arrangement, not an additional legal entity type.

## Target architecture and remaining implementation

1. **Unified workspace:** extend the implemented account-bound intake/progress into
   durable service orders, documents, approvals and team-authorized workspaces.
   Production must apply `g0001` then reviewed `g0002`; the new head does not replace
   or rewrite the original baseline.
2. **Document vault:** private object storage for bytes; tenant-scoped database
   metadata, access checks, malware/file validation, retention and deletion controls.
   Paid storage activation requires approval. Do not put document bytes in SQL.
3. **Genesis AI:** extend the existing server-side AI adapter with model selection,
   grounded service knowledge, structured outputs, cost limits and explicit approval
   before any billable activation. Clearly distinguish rules, assumptions and verified facts.
4. **Service orchestration:** normalized service orders and provider adapters,
   signed webhooks, idempotency, reconciliation, document/signature/KYC handoffs,
   explicit submission consent and evidence-backed completion.
5. **State formation:** obtain authorized provider coverage and current requirements
   by state/entity. Do not claim government API access or 50-state filing capability
   from the current dropdown. IRS EIN guidance is not an automated filing service.
6. **Professional oversight:** licensed legal, tax, accounting, insurance and financial
   review workflows. Define provider scope, referral eligibility and agreements before
   offering regulated services or commissions.
7. **Revenue/admin:** owner-only package/pricing configuration, consulting/subscription/
   service orders, provider-confirmed payments, refunds, receipts, transaction ledger,
   referral disclosures and partner settlement. Amounts remain unset; checkout is disabled.
8. **Production:** approved hosting configuration; real PostgreSQL and reviewed migrations;
   secure production secrets/origins/cookies; HTTPS/proxy/header verification;
   managed backups and a safe restore test; then authorized publishing and live checks.

Existing SQLite data must not be migrated or deleted without an approved, data-preserving
plan. Do not downgrade a populated production database to the initial baseline.

## Acceptance criteria

- **Account/intake:** existing session controls work; explicit saving consent is
  recorded; four questions appear one at a time; invalid/failed saves do not advance;
  reload resumes; two tabs cannot silently overwrite each other.
- **Mission Control:** saved answers/plan are restored after sign-in; draft preparation
  is distinct from real service execution; unquoted fees are never represented as free;
  downloads contain the actual saved data and honest status.
- **Passport:** another tenant or user cannot access the intake; stable business
  details are reused only after authorization; records remain user-provided until verified.
- **Future execution:** an actual provider acknowledgment is required for submitted/
  pending; approval/completion require appropriate evidence; consequential actions
  require explicit consent and approved fees; retries cannot duplicate purchases/filings.
- **Future voice/AI:** unavailable capabilities are explicit; speech requires opt-in;
  model/provider output does not become legal, tax or financial advice by relabelling it.
- **Launch:** automated critical-journey tests plus actual participant accessibility
  and usability studies, approved production configuration, restore verification,
  provider verification, and explicit publishing approval. Automated browser checks
  are not a substitute for real-user studies.

## Verification performed

- Twelve new isolated API tests passed, including all 50 state choices, three stages,
  validation, honest availability, no saved plans and no simulated completion.
- Eleven additional saved-journey tests cover consent, resume, ownership/tenant
  isolation, CSRF, stale-write protection, preferences, lockdown and no fake completion.
- Disposable PostgreSQL `g0001` → `g0002` upgrade preserved a seeded baseline business.
  The new table was initially empty, the revision check passed, and `alembic check`
  reported no schema drift.
- Frontend TypeScript check and multi-entry production build passed using the
  service's declared `PORT=19183` and `BASE_PATH=/`.
- Both managed services restarted successfully.
- Live catalog and plan requests succeeded without sign-in or database writes.
- Desktop and mobile preview screenshots were checked.
- Browser journey passed against disposable PostgreSQL: registration, saving consent,
  one-question intake, reload/resume, Spanish/detail preferences, prepared plan and
  actual text download, logout/login restoration and a controlled failed-save retry.
- Mobile 402px checks found no horizontal overflow and confirmed visible keyboard focus.
  Voice was unsupported in the test browser; no external speech request was made.
- Pre-existing records in both SQLite databases matched the pre-change snapshots.
  The new actual application journey table remained empty: browser-QA writes were
  isolated in disposable PostgreSQL and the temporary QA bridge was removed.
- The prior dependency-remediation suite was not rerun.

Not verified: actual provider execution, professional delivery, AI output, government
filings, live microphone quality, real-user accessibility/usability studies, production
database, production restoration or a published customer journey.

## External costs — indicative, not activated

Published provider prices reviewed on 2026-10-14; actual contracts and usage control costs.

| Item | Current reference / budget basis |
| --- | --- |
| SendGrid Email API | Essentials starts at $19.95/month; Pro starts at $89.95/month. A time-limited trial is not a permanent production allowance. |
| Square US Online API | Published standard card processing reference is 2.9% + $0.30 per transaction; other channels, countries and contracts differ. |
| IRS EIN | Free when obtained directly through the official IRS service. |
| Replit hosting / PostgreSQL | Usage-based. Reviewed documentation quotes a $1/month Autoscale base, $0.60 per million compute units, PostgreSQL storage $0.35/GiB/month and database compute $0.16/hour. Not an application-level monthly quote. |
| AI, documents/storage, domains | Provider/model, volume, retention and domain choices are not approved; estimate after those choices, before activation. |
| Formation, agents and regulated professionals | State/entity fees and qualified-provider quotes are required. No universal 50-state price is verified. |

Sources:
- https://www.twilio.com/en-us/products/email-api/pricing
- https://squareup.com/us/en/payments/our-fees
- https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number
- https://docs.replit.com/billing/aug-cloud-billing-updates
- https://docs.replit.com/billing/about-usage-based-billing

No purchase, subscription, commission agreement or transaction was initiated.
