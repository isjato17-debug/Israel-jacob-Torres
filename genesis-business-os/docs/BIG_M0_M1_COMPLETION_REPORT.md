# B.I.G. M0 and first M1 vertical slice

## Scope and source control

- Starting commit: `95b192cefc018145c4c054db31b643aac4225428`.
- Starting GitHub development commit: `9a81e39e2314365a02d22369946314b3c32bd4f4`.
- Branch: `genesis-os-2-development`, unchanged.
- Ending commit is supplied in the final delivery and generated downloadable report
  after committing this source report; a commit cannot contain its own identifier.
- No push, credential change, branch creation/rename, force-push, main merge,
  deployment or publishing is part of this delivery.
- Both directive uploads are preserved byte-for-byte.

The authorized implementation is M0 plus an initial M1 customer journey, not M2–M10.
No live AI, paid service, government/tax filing, payment or outside-provider activation
is implemented or enabled. The full lifelong business architecture remains in the
master directive and prior design documents.

## Existing feature preservation

The inspection inventory is `BIG_M0_FEATURE_PRESERVATION.md`. A source-level comparison
against the starting commit confirms all **77 pre-existing API route decorators remain**.
The legacy workspace, guided Start/Run/Grow, guest drafts, six-language saved consultations,
voice support, Founder DNA/readiness, Digital Twin, Executive Board, Battle Mode, Failure
Lab, financial scenarios, Mission Control, actuals/variance/decision ledger, route/evolution
engine, community, evidence/approval controls, owner campaigns, Partner Network,
internal co-marketing, official discovery, Square foundations and security protections
remain. Their regression suites passed; this is not a claim of production certification
or live AI/provider operation.

Legacy Business access is additionally customer-restricted for **new private projects**.
Existing businesses retain their prior tenant-sharing behavior. Private project lists,
Mission Control, twin/scenario/tasks, decisions and execution endpoints enforce the
new project owner's identity, not merely tenant membership.

## Implemented customer journey

New additive customer route: `/next/ideas/`, linked from the existing guided header.

1. Existing account sign-in, explicit consent, private saved multiple ideas.
2. Concept, industry, state/DC, integer-cent budget, goals, preferences, notes and
   planning assumptions; created/updated dates and saved revision metadata.
3. Edit before development, archive, restore, reopen, compare strategies and resume.
4. Three deterministic plans: **Start Smart**, **Build Strong**, **Grow Big**.
5. Itemized startup allowances, itemized fixed monthly overhead, variable delivery
   cost estimate and total monthly expense display.
6. Ticket and volume assumptions, lower/base/higher revenue scenarios, gross margin,
   operating profit, break-even revenue, reserve and funding gaps.
7. Recommendation with reasons; customers may choose any prepared plan, including
   one with a funding gap. No spending is authorized by selection.
8. Initial review-needed business requirements and existing Partner Network service
   category vocabulary. New York and cleaning-safety prompts supplement general guidance.
9. Selected assumptions preserved in a persistent Business Project. Existing Business
   and financial twin records are reused, not duplicated with a replacement business system.
10. Seven initial Mission Control tasks with persistent done/to-do state and zero
    authorized spend. Repeated project creation safely returns the same project.
11. Primary Ask B.I.G., My Businesses and Review Decisions controls. Review Decisions
    shows real saved plans awaiting selection/project creation, **not** a fabricated
    external approval inbox. Advanced existing routes remain in secondary navigation.
12. Explicit error recovery, server-owned identities, optimistic versions, account
    switching cleanup, old-session response guards, focus refresh and mobile layout.

The $3,000 New York cleaning example yields:

| Plan | Startup allowance | Monthly fixed overhead | Reserve | Funding required | Gap |
|---|---:|---:|---:|---:|---:|
| Start Smart | $1,625 | $550 | $550 | $2,175 | $0 |
| Build Strong | $4,000 | $1,210 | $2,420 | $6,420 | $3,420 |
| Grow Big | $9,000 | $2,200 | $6,600 | $15,600 | $12,600 |

These are **unverified template estimates**, not quotes, legal requirements, verified
transactions, AI-generated research, or success promises. Variable-cost cash timing,
owner compensation, taxes, debt service and jurisdiction-specific fees may require
additional cash beyond these allowances.

## Consultation privacy repair

No recoverable revoke/delete implementation was found in this checkout or available
branch history. Added an explicit privacy decision endpoint and visible, localized
confirmation controls in all six existing consultation languages.

- **Withdraw:** blocks future consultation saving/processing; existing transcript
  remains visible read-only to its customer.
- **Erase saved transcript:** requires separate confirmation; clears consultation
  questions and responses while keeping the consultation identity/version tombstone,
  privacy choice and minimal audit metadata.
- Intake, business, financial, partner and unrelated customer records are not erased.
- **Give consent again:** explicit new decision before resuming. A stale consent checkbox
  or delayed request cannot restore erased/withdrawn content.
- Privacy choices and saves serialize through the same journey lock; both privacy
  and consultation versions are checked. In-flight deletion regression passes.
- CSRF, user/tenant isolation, strict fields, authentication and lockdown are retained.
- Privacy audit records contain status/version, not messages or business facts.

This is saved-consultation privacy, **not** account-wide deletion, a Business Passport,
automatic retention, a document vault or certified legal compliance. Existing backups
can retain older data; deletion-aware retention/restore remains an explicitly disclosed
separate requirement. The UI warns about this limitation.

## Database changes and preservation

New models/tables only:

- `ConsultationPrivacy` / `consultation_privacy`
- `BusinessIdea` / `business_ideas`
- `IdeaRevision` / `idea_revisions`
- `BusinessProject` / `business_projects`

Existing `Business`, `ExecutionTask` and minimized `AuditEvent` are reused for newly
created records. Existing consultation rows are only changed when their customer
explicitly invokes privacy controls.

Additive migration: `g0006_private_ideas_and_consent.py`, after unchanged `g0001` through
`g0005`. It creates four tables and indexes; it does not rewrite or delete original rows.
Downgrade refuses to remove populated new tables.

Before editing: both SQLite integrity checks passed; root database had 18 tables
and zero rows, application database 23 tables and 154 rows. Recovery copies, original-row
snapshots and a Git bundle are excluded under `generated-artifacts/m0-preservation/`.
Both originals also had zero foreign-key violations.

Disposable SQLite and PostgreSQL migration tests verify preservation from `g0003`
through `g0006`, including seeded journey, campaign, consultation, partner and promotion
records, empty new tables, Alembic head and no metadata drift. Browser writes use a
separate disposable SQLite database; no real customer is used for QA.

Final read-only comparison confirmed **all 154 original application rows unchanged across
all 23 original tables**, and the root database's 18 original tables still empty.
Both integrity checks passed and both had zero foreign-key violations. The four new
application tables are empty in normal development; all QA stayed separate.
The disposable browser database was removed, the disposable PostgreSQL database dropped,
and its temporary server stopped. Normal SQLite configuration and the exact original
`.replit` were restored. API readiness returned HTTP 200 with database/schema true;
both managed workflows restarted cleanly.

## Verification

- Full backend regression suite: **142 passed**, including SQLite and PostgreSQL migration
  tests; no skipped PostgreSQL case in that run.
- After the final category/industry refinements and additional financial-boundary and
  bakery regressions: **18 affected Idea Vault tests passed**. This focused final pass
  does not claim a second full regression run.
- Separate execution-layer regression suite: **3 passed**.
- Frontend TypeScript and production build passed.
- Financial assertions cover item sums, zero/one-cent/exact-cent/high-budget inputs,
  gross-margin scenario arithmetic, funding gaps and existing partner-category keys.
- Privacy assertions cover withdrawal, deletion, explicit re-consent, stale/in-flight
  reply prevention, before-first-turn deletion, CSRF, authentication, isolation,
  lockdown, retained intake and minimized audit.
- Ownership tests cover another tenant and a different customer in the **same tenant**,
  including legacy Business/Mission Control endpoints for new private projects.
- Signed-out iPhone-sized screenshot confirmed the new route loads and sign-in renders.
- Authenticated browser acceptance passed at 390×844 and 1280px: the exact saved cleaning
  idea, $3,000 budget, three plans, Build Strong selection/project, persisted task, reload
  and logout/login resume, second idea edit/archive/restore/history, Review Decisions,
  different-customer isolation, and privacy withdraw/erase/re-consent all passed.
  Arabic RTL and Spanish interface/English-assessment disclosure were checked.

The mobile pass initially found horizontally overflowing plan cards; zero-minimum grid
tracks, wrapping references and bounded table columns were corrected. It is reported
as a development defect, not silently excluded from the evidence.

The browser pass also found cleaning-specific wording in the generic New York prompt
for a bakery idea. The prompt was made industry-neutral, bakery/baking inputs now reuse
the existing food template, and food-business review guidance plus a focused regression
were added. Existing saved plan snapshots are not silently rewritten. Changing the guided
language correctly marks older consultation context stale; saved answers remain unchanged.

Nonblocking pre-existing warnings: Starlette/httpx test-client compatibility, Passlib's
Argon2 version lookup and Alembic's legacy path-separator default. An initial shell build
without the workflow-required PORT/base values failed; the build passed with the existing
artifact's values. No runtime configuration was weakened to bypass it.

## Security and integration audit

New routes use existing sessions, tenant/customer ownership, CSRF, strict Pydantic inputs,
bounded text, integer-cent budgets, minimized audits and lockdown. No new secrets,
identity documents, financial account details, tax identifiers or uploads are requested.
Shared production throttling is still not implemented; existing rate limiting remains
process-local. No independent penetration test or production-security certification
was performed.

| Capability | Observed classification |
|---|---|
| New three-plan engine | Deterministic local calculations; no network or live AI |
| Existing saved consultation | Rule-based zero-charge simulation; live AI disabled |
| SendGrid | NOT_CONFIGURED in current local catalog |
| Square | NOT_CONFIGURED in current local catalog; existing architecture preserved |
| Checkout | Disabled / PRICING_NOT_APPROVED |
| Partner relationships | Private/manual attestations; not live API connections; ACTIVE blocked |
| SBA, IRS, NY, OSHA and state/DC references | Public-information references, not verified filing/service connections |
| Government/professional execution | No new live integration, submission, authorization or charge |

## Files

Frontend:
`IdeaVault.tsx`, `ideas.css`, `ideas-api.ts`, `PrivacyControls.tsx`, `privacy-i18n.ts`,
`ConsultationPanel.tsx`, `consultation-api.ts`, `GuidedExperience.tsx`, `entry.tsx`,
and `vite.config.ts` under `artifacts/genesis-app`.

Backend:
`app/models.py`, `app/main.py`, `app/services/idea_planning.py`,
`app/services/readiness.py`, `app/v2/ideas.py`, `app/v2/consultation_privacy.py`,
`app/v2/consultation.py`, the new `g0006` migration, `tests/test_idea_vault.py`,
`tests/test_consultation_privacy.py` and expanded `tests/test_big_migration.py`.

Documentation:
this report, `BIG_M0_FEATURE_PRESERVATION.md`, and the existing project-scope memory.
The final commit file list is authoritative.

## Unfinished and next milestone

- New Idea Vault controls are English/Spanish; saved plan assessments currently remain
  English. Existing consultation/guided six-language support is preserved. New privacy
  translations need fluent-speaker review.
- Estimates use industry templates, not free-form reasoning, verified market research
  or supplier quotes. Text goals/preferences are preserved but not intelligently interpreted.
- Per-line assumption editing, cross-idea side-by-side comparison, broader localization,
  list pagination and more extensive usability studies are not part of this initial slice.
- Requirements are initial review prompts, not the M2 versioned legal requirements registry.
- Review Decisions is not the M3 unified external-approval inbox. Projects are in PLANNING;
  no registration, launch or real-world completion is claimed.
- Backup-aware deletion recovery, shared production limits, production migrations,
  certified translations/accessibility and verified live providers remain separate work.
- The five-minute target was not established by a real-user usability study.

Recommended next development: finish bounded M1 plan-assumption editing and localization,
then re-evaluate acceptance. Do not start M2–M10 or live activation without authorization.

Canonical baseline remains **400 PASS / 0 FAIL / 600 RELEASE GATE**; these are not a
product-completion percentage. This delivery does not reclassify those canonical gates.
