# Genesis OS 2.0 — reconstruction blueprint and development status

> Current customer brand: **B.I.G. — Business Inside Genesis**, powered by Genesis OS 2.0.
> The newer authorized no-cost Phase 2 slice is documented in `BIG_PHASE2_IMPLEMENTATION.md`.
> Historical verification below describes earlier milestones, not a new combined certification.
> GitHub branch rename/synchronization at the prior baseline was completed; do not repeat it.
> Current additive migrations extend `g0001 → g0002 → g0003` with `g0004 → g0005`.
> Partner foundation boundaries are in `BIG_PARTNER_NETWORK_FOUNDATION.md`.

## Scope and safety

The master directive authorizes reconstruction of the existing product, not a second
project or repository. Start, Run and Grow are the primary customer journeys.
The supported initial journey is account creation/sign-in, consented one-question intake,
saved progress and a prepared launch checklist. A separate private operator console now
supports campaign planning and internal content review. This is not the completed ecosystem.
No paid services, government filings or publication have been authorized or performed.

The existing interface, accounts, business records, community, execution workflows,
tenant boundaries, CSRF/session controls, approvals and audit system remain in place.
The original reconstruction preserved the legacy frontend. The newer B.I.G. phase updates
customer-facing branding and truthful provider labels while preserving legacy functionality.

- Stable `main` baseline: `7a09fa54d0a18dad7f5b6cca184d8258f7c47418`.
- Reconstruction branch: `genesis-os-2-development`.
- Existing application: `/`.
- Guided development experience in the same application: `/next/`.
- Preserved original guest draft/service discovery: `/next/draft/`.
- Private operator planning console: `/next/owner/`.
- Latest pre-change local recovery snapshot: `generated-artifacts/backups/20261015T021302Z/`.
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

Historical recovery procedure only (no longer pending): use one supported GitHub CLI device flow with an explicit configuration directory in
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
- Private Infinite Growth planning: real saved campaigns, original draft content,
  planned USD budgets stored as integer cents, and a reversible review/archive lifecycle.
- Platform access is explicitly designated; a customer registering as a business
  `owner` never automatically receives platform-owner permissions.
- Internal review requires confirmation. Editing clears prior approval. Archive preserves
  records; reopen returns them to draft. Stale edits cannot silently replace newer data.
- Campaign planning does not authorize spending or external publishing. No AI generation,
  trend detection, social posting, verified performance feed or revenue measurement is connected.
- Additive `g0003` campaign migration follows `g0002`; neither replaces the `g0001` baseline.

**Important:** State selection is not state-specific formation coverage. The checklist
is selected by business stage; it is not tailored legal advice or AI-generated advice.
The user's goal is shown as context, not used to imply intelligent personalization.
No service is shown as connected merely because an adapter or credential field exists.
Journey status `PREPARED` means a preliminary plan exists. Every listed service is
`NOT_STARTED`. The new API does not accept customer-written submission/completion
statuses. Future `SUBMITTED`, `PENDING`, `APPROVED` and `COMPLETED` transitions require
provider acknowledgments or appropriate professional evidence, not a progress checkbox.

## Ten core systems and owner-growth blueprint

| System | Reusable foundation / implemented slice | Remaining work |
| --- | --- | --- |
| Mission Control | Existing accounts, businesses, audit/approval/execution records; new saved journey and truthful cost/progress view | Unified service orders, deadlines, provider receipts, owner reporting and alerts |
| Business Brain | Account-scoped consented intake and user-provided context | Permission-controlled business memory, explicit sharing/retention/revocation, authorized personalized consulting and source provenance |
| Adaptive Intelligence | Saved language/detail preferences, progressive intake, optional browser speech | Authorized model, conversational reasoning, grounded personalization and accessibility research with real users |
| Business Autopilot | Existing risk tiers, explicit approvals and SendGrid/Square execution adapters | Durable task orchestration, provider contracts, consent scopes, idempotent submissions/webhooks and reconciliation |
| First Customer Engine | Existing business/route context | Consent-aware lead/opportunity records, outreach planning, connected channels and actual opportunity/sales evidence |
| Financial Command | Existing business records; no connected financial feed claimed | Authorized accounting/banking data, sourced cash-flow analysis, invoicing/payroll coordination, refunds and separate government/provider/platform fees |
| Business Health Monitor | Existing business records and security controls | Verified jurisdictional obligations, sourced deadlines, finance feeds, scheduled checks and explainable risk alerts |
| Business Passport | Consented reuse of the same user's self-reported intake | Private document vault; field-level sharing permissions; provenance, verification, expiry and revocation |
| Enterprise Architect | Existing multiple-business records; distinct legal-entity/ownership choices | Parent/subsidiary/brand relationships, ownership interests, permissions and professionally reviewed expansion plans |
| Business Network | Existing community foundation; no approved marketplace claimed | Optional participation, approved/vetted professionals and suppliers, permissioned introductions, provenance and disclosures; no automatic sharing of private business information |
| Infinite Growth (owner system) | Private campaign drafts, planned budgets, internal review, audit and archive/reopen | Authorized trend discovery, original AI-assisted content, social connections, consented success stories, eligible referrals/affiliates, actual analytics, retention signals and controlled experiments |

Self-reported information is never labelled verified. A holding company is an
ownership arrangement, not an additional legal entity type.

The subsequent complete reconstruction directive supplies all seven phases and supersedes
the earlier truncated phase text. Follow this order for remaining work:

1. Preserve/security audit and GitHub recovery. Local safeguards and Git transport
   synchronization at the prior baseline were verified. Branch rename is complete;
   a missing CLI login alone is not grounds to repeat authorization.
2. Premium customer experience, genuine Genesis AI, Adaptive Intelligence, Mission
   Control and Business Passport. The saved guided journey is implemented; connected
   AI, verified document reuse and a secure vault are not complete.
3. Verified formation and outsourced-service workflows.
4. OnePay, approved professional marketplace, purchased-service tracking and full
   owner administration. See `GENESIS_ONEPAY_ARCHITECTURE.md` for the researched Stripe
   Connect recommendation, Square preservation strategy and required legal/approval gates.
5. Financial tools, business management, growth intelligence and multi-company support.
6. Infinite Growth and advanced automation. The already-developed campaign planning
   foundation is retained, but further automation does not take priority over Phase 2.
7. Security, accessibility, integration and genuine production testing/acceptance.

Purchased-service states must distinguish PAID, ASSIGNED, IN PROGRESS, SUBMITTED and
COMPLETED, with additional failure, verification, customer-action and refund states.
Payment confirmation is not proof of professional delivery or government approval.

## Modular reconstruction and growth boundaries

- Keep legacy functionality operational while the new experience matures. A later
  default-interface cutover requires acceptance of the completed supported journeys;
  the current parallel development route is not a claim that reconstruction is finished.
- Domain boundaries: customer workspace/business memory; consent and document provenance;
  service orders and evidence-based execution; professional/provider adapters; financial
  ledger and payments; health monitoring; company relationships; optional network;
  and platform-operator growth management.
- Shared foundations: existing authentication/tenant boundaries, explicit operator
  authorization, audit events, optimistic versions, reviewed migrations, typed client
  contracts and testable state transitions. Do not embed provider secrets in browser code.
- Start with English/Spanish. Keep translation keys outside components and extend the
  supported-locale contract deliberately when additional languages are actually supported.
- Target **WCAG 2.2 AA**: clear labels, visible/unobscured focus, keyboard operation,
  appropriate target sizes, contrast, accessible validation, reduced motion and readable
  language. Automated spot checks are not a conformance certification or participant study.
- Infinite Growth must not generate fake engagement, misleading testimonials, spam,
  unauthorized publishing or promises of permanent virality/guaranteed growth.
- Success stories require recorded permission and appropriate review. Experiments need
  hypotheses, consent/analytics review, approved limits and real measured outcomes.
  Internal content approval alone never authorizes external publication or paid spend.

## Private owner authorization

`GENESIS_PLATFORM_OWNER_USER_IDS` is a server-side, non-secret allowlist of explicitly
approved account IDs. The account must also have an active owner/admin session. It is
empty by default; no real customer account was designated as operator during development.
All campaign operations additionally remain tenant scoped, CSRF protected and lockdown aware.

To designate the actual operator, the user signs in to Genesis, visits `/next/owner/`
and identifies their own account using the Copy ID control. After explicit designation,
configure the allowlist through the supported environment-variable flow. Never infer the
platform operator from a newly registered tenant-owner role or read/print credentials.

The access page exposes only the signed-in account's own ID. There is no browser-side
“make me platform owner” action. Only disposable QA accounts were allowlisted for testing.

## Target architecture and remaining implementation

1. **Unified workspace:** extend the implemented account-bound intake/progress into
   durable service orders, documents, approvals and team-authorized workspaces.
   Production must apply reviewed `g0001` → `g0002` → `g0003`; the new head does not replace
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
- **Private growth:** customer owners are denied without explicit platform designation;
  campaign records persist; budgets are validated exactly; review needs confirmation;
  edits invalidate approval; stale writes preserve user input; archives are reversible;
  spending, publication and unverifiable performance remain unavailable.
- **Launch:** automated critical-journey tests plus actual participant accessibility
  and usability studies, approved production configuration, restore verification,
  provider verification, and explicit publishing approval. Automated browser checks
  are not a substitute for real-user studies.

## Verification performed

- Twelve new isolated API tests passed, including all 50 state choices, three stages,
  validation, honest availability, no saved plans and no simulated completion.
- Eleven additional saved-journey tests cover consent, resume, ownership/tenant
  isolation, CSRF, stale-write protection, preferences, lockdown and no fake completion.
- Fourteen operator tests cover default-deny access, role/allowlist separation,
  tenant isolation, CSRF, exact budget limits, review, approval invalidation,
  reversible archives, stale writes, lockdown and disabled external publishing.
  The combined targeted suite passes 37 cases.
- Disposable PostgreSQL `g0001` → `g0002` upgrade preserved a seeded baseline business.
  The new table was initially empty, the revision check passed, and `alembic check`
  reported no schema drift.
- Disposable PostgreSQL `g0002` → `g0003` upgrade preserved both a baseline business
  and an existing saved journey. The campaign table was initially empty, the revision
  check passed, and `alembic check` again reported no schema drift.
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
- The private owner campaign browser journey passed against isolated PostgreSQL:
  customer-owner denial, authorized creation/reload, exact budget, review/approval,
  edit invalidation, actual stale-write conflict/rebase, archive/reopen, Spanish,
  logout/login restoration and 402px keyboard/overflow spot checks.
- Pre-existing records matched the latest pre-change snapshots. The actual application
  campaign table remained empty; QA writes were isolated. Temporary QA routing and
  servers were removed after testing. No real account was granted operator status.
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
