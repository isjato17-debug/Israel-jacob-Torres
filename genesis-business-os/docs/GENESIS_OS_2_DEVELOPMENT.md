# Genesis OS 2.0 — first development milestone

## Scope and safety

The master directive authorizes reconstruction of the existing product, not a second
project or repository. Start, Run and Grow are the primary customer journeys.
This milestone is a functioning discovery/planning preview, not the completed ecosystem.
No paid services, government filings or publication have been authorized or performed.

The existing interface, accounts, business records, community, execution workflows,
tenant boundaries, CSRF/session controls, approvals and audit system remain in place.
The existing HTML, JavaScript and CSS frontend files are unchanged.

- Stable `main` baseline: `7a09fa54d0a18dad7f5b6cca184d8258f7c47418`.
- Reconstruction branch: `genesis-os-2-development`.
- Existing application: `/`.
- Isolated preview in the same application: `/next/`.
- Local recovery snapshot: `generated-artifacts/backups/20261015T013632Z/`.
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

## Preserved architecture

- **Current frontend:** existing HTML/JavaScript under `frontend/`, served by Vite.
- **Preview:** React/TypeScript components in the existing web artifact, with a
  separate Vite HTML entry. Production output retains both HTML entries.
- **Backend:** existing FastAPI application and SQLAlchemy models, not a database
  replacement or a new authentication stack.
- **Persistence:** existing tenant/business records remain authoritative. Preview
  discovery and checklist generation are deliberately stateless.
- **Existing provider adapters:** SendGrid and Square execution remains approval-
  and evidence-oriented. No provider is certified operational by this milestone.

## Completed in this milestone

- Start / Run / Grow mobile-first discovery and intake interface.
- Search/filter across 17 business service categories.
- Planning intake for all 50 states, with legal entity and ownership structure
  represented separately. Holding companies/subsidiaries are ownership descriptions,
  not additional legal entity types.
- Real `GET /api/v2/catalog` and `POST /api/v2/plan` endpoints.
- Preliminary stage-based checklists and an explicit unsaved text download.
- Validation, errors, loading states, professional-review flags and official guidance.
- No external execution, checkout, AI calls, saved customer answers or new DB schema.

**Important:** State selection is not state-specific formation coverage. The checklist
is selected by business stage; it is not tailored legal advice or AI-generated advice.
The user's goal is shown as context, not used to imply intelligent personalization.
No service is shown as connected merely because an adapter or credential field exists.

## Target architecture and remaining implementation

1. **Unified workspace:** bind the new journeys to existing accounts/businesses.
   Persist structured intake, plans, progress, service orders and consent records.
   Define migrations after model review; preserve the existing production `g0001`
   baseline and apply subsequent reviewed migrations explicitly.
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
8. **Production:** approved hosting configuration; real PostgreSQL and `g0001`;
   secure production secrets/origins/cookies; HTTPS/proxy/header verification;
   managed backups and a safe restore test; then authorized publishing and live checks.

Existing SQLite data must not be migrated or deleted without an approved, data-preserving
plan. Do not downgrade a populated production database to the initial baseline.

## Verification performed

- Twelve new isolated API tests passed, including all 50 state choices, three stages,
  validation, honest availability, no saved plans and no simulated completion.
- Frontend TypeScript check and multi-entry production build passed using the
  service's declared `PORT=19183` and `BASE_PATH=/`.
- Both managed services restarted successfully.
- Live catalog and plan requests succeeded without sign-in or database writes.
- Desktop and mobile preview screenshots were checked.
- Logical contents of both existing SQLite databases matched their recovery snapshots.
- The prior dependency-remediation suite was not rerun.

Not verified: authenticated new account-bound persistence (not implemented), actual
provider execution, professional delivery, AI output, government filings, production
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
