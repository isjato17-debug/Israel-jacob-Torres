# B.I.G. Master Orchestrator — verified local development

## Scope and source control

Starting commit: `ad4d0079d46e08df934d9d3448f6ff38d05dad7e`.
Existing AutoForm delivery `f1ac23e026e6c34ba0c9a8a7a7bcb32248d71af3`
is its ancestor, not assumed to be on GitHub. Work stays on
`genesis-os-2-development`. The ending local commit is supplied in final delivery.
No push, force-push, branch deletion/rename, merge into protected main, deployment,
paid activation, real signature, government/financial submission or payment was performed.

The owner's latest instruction is to finish the pending implementation, fix failures,
run regression/TypeScript/build verification and commit verified work locally.
The uploaded master directive supplies the bounded customer journey, not permission
to activate all future business services.

## Functioning implementation

### Persistent coordination

Five core project actions coordinate strategy review, document preparation,
exact-revision approval, TEST signing and TEST submission. They reuse existing
`ExecutionActionRecord` / `ExecutionReceiptRecord` and existing Mission Control
tasks, rather than replacing the execution hub. `ProjectAction` adds project
dependency metadata, requirements, subsystem, version, attempts, optional deadline
and completion time around that shared action record.

Supported status vocabulary includes NOT_READY, INFORMATION_REQUIRED, READY,
AWAITING_CUSTOMER_APPROVAL, AUTHORIZED, IN_PROGRESS, AWAITING_EXTERNAL_RESULT,
COMPLETED_VERIFIED, CORRECTION_REQUIRED, FAILED and CANCELLED. Only supported
transitions have mutation endpoints; clients cannot assign arbitrary statuses.
Core dependencies are processed in a deterministic topological order.
Regulatory review actions are independent of document preparation.

Explicit initialization is idempotent. Prerequisites, optimistic version checks,
request-key uniqueness and immutable package hashes prevent duplicate test work.
Legacy approval endpoints cannot bypass project authorization. Old action listings
do not expose these private project actions to other same-tenant customers.

### Existing intelligence and AutoForm

The three-plan engine supplies genuine deterministic comparisons and recommendation
reasons, funding gaps, assumptions and risks. The customer explicitly reviews
alternatives and retains the existing selected plan; this does not overwrite it.
The same existing project screen retains its financial/Digital Twin, Executive Board,
Founder DNA availability and Passport/document interfaces.

No live AI, market research, legal eligibility or profitability is fabricated.
Evidence gaps and mitigation are visible. This is an initial financial strategy
connection, not an implementation of every future strategic domain.

The existing Cleaning Service Agreement renderer, historical source hashes,
corrections, downloads and exact-document approval remain intact. Existing
document-save/generate/approve transactions update initialized orchestration state
in the same transaction. Corrections invalidate downstream readiness while
retaining prior signed-test copies and evidence.

### No-cost TEST signing

The customer sees the complete disclosure and exact document hash, supplies the
exact provider representative name, expressly confirms review and test consent,
and reauthenticates with their account password. Password failures are rate limited.
The server never stores that password, raw biometrics or device biometric templates.

An immutable structured envelope binds project, customer, document ID/hash,
disclosure version, consent, authentication method and timestamp. Its printable
TEST copy has a reproducible SHA-256 and server HMAC audit evidence using an
existing runtime secret, never exposed in responses. Private downloads verify
integrity and use attachment/no-store headers. Consent withdrawal blocks further
test processing; historical copies and withdrawal evidence remain accessible.

This is **not a legally executed contract**, a customer/client countersignature,
independent identity verification, a qualified signature, agency-accepted e-signature
or an independent timestamp certificate. Passkeys/WebAuthn/Face ID/Touch ID are
explicitly **NOT IMPLEMENTED**. No paid signature provider was activated.
Production signing still needs method/legal/provider review and audit-key lifecycle
planning. A server HMAC is tamper evidence within the server's trust boundary,
not independent nonrepudiation.

### DirectSubmit TEST adapter

Separate customer authorization binds the exact current non-withdrawn test-signed
package. Dispatch records one local attempt and moves to AWAITING_EXTERNAL_RESULT.
A separate verify step produces SIMULATED_ACCEPTED, SIMULATED_REJECTED or
SIMULATED_CORRECTION_REQUIRED, with TEST-prefixed reference and package hash.
Negative results remain negative; retries require a new authorization/request key.
Cancellation preserves history. No network submission, government credential,
filing fee or payment exists in this adapter.

COMPLETED_VERIFIED for a simulated action means only its **local TEST result**
was verified. The UI labels this TEST_ONLY and displays the synthetic receipt.

### Official-source collection and review

The existing fixed Federal Register read remains. Customer-initiated collection
records official notice metadata and a bounded New York Department of Labor
minimum-wage update excerpt. URLs, facts, content hash and verification time are
preserved as immutable source revisions. Repeated identical content is deduplicated;
changed content links the prior revision. Integrity failures block review.

First collection is FIRST_SOURCE_OBSERVATION, **not proof of a new legal change**.
The pipeline creates a possible-relevance review action and existing Mission
Control task, without asserting that a notice applies or inventing a deadline.
REVIEWED / NOT_APPLICABLE can close the review task; NEEDS_PROFESSIONAL_REVIEW
keeps work outstanding. Review is not legal advice or compliance certification.

Actual effective legal obligations are not automatically updated. Current live
source metadata is UNVERIFIED for applicability; proposed rules must not be treated
as effective law. Actual content-difference handling is tested with explicitly
synthetic source fixtures; no fabricated historical law change is claimed.
There is no autonomous background monitoring, external notification, automatic
document correction or automatic filing.

## Government findings and registry boundaries

Official pages were independently fetched on 2026-10-15:

- NY LLC Articles of Organization:
  https://dos.ny.gov/articles-organization-domestic-limited-liability-company-0
- NY LLC formation instructions:
  https://dos.ny.gov/forming-limited-liability-company-new-york
- Domestic business corporation:
  https://dos.ny.gov/certificate-incorporation-domestic-business-corporation
- Ongoing biennial statements:
  https://dos.ny.gov/biennial-statements-business-corporations-and-limited-liability-companies
- NY business/tax starting points:
  https://www.tax.ny.gov/bus/doingbus/starting_business.htm
- NY wage guidance: https://dol.ny.gov/minimum-wage

County-level discovery:
https://www.albanycountyny.gov/fees-forms
County-specific certificate, notarization, submission and fee requirements remain
unverified; no statewide sole-proprietor formation requirement is fabricated.

The registry distinguishes the supported B.I.G. agreement from an **official
reference only** for LLC articles; no verified government PDF revision/autofill is
claimed. It carries categories, jurisdiction, eligibility caveats, mapping/field
requirements, conditional questions, supporting-document/signature/submission
requirements, fees and renewal notes.

NY LLC is the first customer-assisted integration **candidate**, because official
instructions describe organizer signing, an online filing path and official filing
receipt. This is not a structure recommendation for every customer. The official
page lists $200 formation, with separately applicable publication/other costs.
Corporation instructions list $125 base filing, with other applicable costs needing
review. Reverify fees before actual work.

No authorized agency submission API or third-party account access was verified.
The next live dependency is an approved exact form/channel, recipient method,
customer authorization and signatures, agency access/terms, fees, sandbox if
available and verifiable receipt/status evidence. Do not automate a portal or
claim an API based only on an online filing link.

## Verification and preservation

- Independently checked the existing commit and baseline before editing.
- Preserved SQLite backups and exact original-row snapshots for both databases,
  plus a pre-change Git bundle under excluded
  `generated-artifacts/orchestrator-preservation/`.
- Original root DB: 18 tables / 0 rows.
- Original application DB: 31 tables / 154 rows; both passed integrity/FK checks.
- All **98 pre-existing route decorators** retained.
- Migrations `g0001` through `g0007` untouched.
- Additive `g0008` creates only five tables: `project_actions`,
  `test_document_signatures`, `test_submissions`, `regulatory_source_revisions`,
  `regulatory_change_records`; no original columns/tables are dropped or replaced.
- SQLite and disposable PostgreSQL migration tests preserve seeded original
  projects, Passport, document source, byte hash and approval; Alembic no-drift
  check passes. Downgrade refuses populated new evidence tables.
- Final backend regression suite: **177 passed**, including both migration tests.
- Execution-layer regression: **3 passed**.
- TypeScript and production build: **passed**.
- Existing nonblocking Starlette/httpx, Argon2 and Alembic configuration warnings remain.

The first PostgreSQL baseline invocation used a database name outside the suite's
safety prefix. It was corrected to a disposable `big_phase2_test_*` name without
weakening that guard. A new tamper-test fixture initially selected a prior QA
project's source; it was corrected to its own exact source revision. Final full
suite is clean. No product security check was removed to obtain passing tests.

Security coverage includes CSRF, password reauthentication, explicit consent,
exact-revision binding, downstream invalidation, HMAC/hash tampering, duplicate
prevention, signature withdrawal, unavailable sources, proposed-rule safety,
same-tenant/cross-tenant privacy, lockdown and minimized audit. No new external
penetration-test or certification claim is made.

Authenticated browser acceptance passed on the exact $3,000 New York cleaning
project with Build Strong retained. The customer corrected $220.25 to $225.75,
approved exact revision 2, completed the disclosed/password-reauthenticated
provider TEST signature and downloaded its integrity-verified private copy.
The unsigned original and old revision remained available.

The local adapter moved through explicit authorization, one dispatch attempt,
AWAITING_EXTERNAL_RESULT and SIMULATED_ACCEPTED. Its package hash matched the
downloaded test artifact; no government receipt was claimed.

Live public-source collection returned four official observations. The New York
record was explicitly reviewed, and the corresponding existing checklist task
became Done. Three other source-review tasks remained pending. All source records
remained FIRST_SOURCE_OBSERVATION / UNVERIFIED, with no invented effective date.
This demonstrates source-backed review, not a verified new effective law.

Logout/UI login restored the same revision, test signature/hash, synthetic receipt,
source review and tasks. Another QA account saw no owner's ideas and received 404
for orchestrator/download; signed-out requests received 401.

Mobile/desktop page client/scroll widths matched: 345/345 at 360px,
375/375 at 390px and 1265/1265 at 1280px. This is browser viewport automation,
not native Safari/Face ID testing or a real-user usability study.

A workspace restart interrupted the initial browser assignment and removed the
temporary `/tmp` PostgreSQL server/data. The same browser assignment resumed its
saved QA journey and completed successfully after the same managed workflows
were restarted. Passing regression results above were already complete before
that restart and code did not change afterward.

All browser writes used an entirely separate disposable database. Its two QA
accounts, single project and test artifacts were removed by deleting only that
disposable file after browser acceptance. Original database files/backups remain.
The temporary environment override was removed, exact original `.replit` restored,
and the normal API restarted cleanly. Final direct comparisons proved every row
of all 18 root tables and all 31 original application tables unchanged: 0 and 154
rows respectively. Both databases passed integrity and FK checks. The application
now has 36 tables: the original 31 plus exactly five new, empty orchestration
tables. No QA data was copied into the original database.

## Source control backup procedure

After committing locally, retain an additional full-history bundle that includes
the final commit:

```
git bundle create generated-artifacts/orchestrator-preservation/verified-source.bundle --all
git bundle verify generated-artifacts/orchestrator-preservation/verified-source.bundle
```

The bundle is intentionally ignored by Git/deployment and can be copied/downloaded
from the workspace. It backs up source history, not private customer database
contents. The separately retained SQLite snapshots cover original development
data. Do not publish those private snapshots.

Check `git ls-remote origin refs/heads/genesis-os-2-development` against local HEAD;
local commits and Replit's internal backup remote are not proof of GitHub sync.
No push is part of this delivery. Future synchronization requires normal reviewed
Git operations and explicit authorization, never force-pushing or credential changes.

## Next authorized implementation work

Complete a real source-change verification/review cycle before claiming effective
legal-change automation. For live signatures/formation, first obtain the separate
method/provider/agency approvals above. Broader official-form autofill, WebAuthn,
professional delivery, live AI and all future business-operation services remain
outside this completed no-cost test slice.
