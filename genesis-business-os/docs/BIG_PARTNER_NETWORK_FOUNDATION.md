# B.I.G. Partner Network — bounded development foundation

## What is implemented versus planned

This is an additive, private, tenant-scoped application/review and promotional-planning
foundation. It is not an operational partner marketplace, government endorsement, licensed
service-delivery platform or connected professional network.

Routes are additive: `/next/partners/` for applicants and `/next/owner/partners/` for explicitly
designated operators. Existing `/`, `/next/` and `/next/owner/` functionality remains.
The new partner surfaces use English/Spanish and disclose that scope; the six-language guided
customer/consultation experience remains. No new logo, public partner page or ad is created.

### Application portal

Twelve categories cover government-authorized service providers, formation companies,
registered agents, attorneys/legal professionals, CPAs, tax professionals, insurance,
banking/lending, payroll/accounting, trademark/patent, technology/AI, and marketing/growth.
Choosing a category is self-reporting, never verification of authorization or licensing.

An authenticated applicant supplies business/contact information, services, state/DC
coverage, professional credentials/license descriptions, API capability descriptions,
partnership interests and indicative pricing. Sensitive documents, identity numbers,
bank details, API keys and tokens are not requested. No upload endpoint exists.
Explicit saving/reviewer-access consent is required; information is not publicly exposed.
The applicant sees only their own submissions within their tenant.

### Private operator command center

The existing server-side platform-owner allowlist and active owner/admin role are both
required; an ordinary customer tenant-owner account does not obtain operator access.
Operators review only applications in their own tenant. This intentionally preserves the
existing owner-console isolation policy. **Cross-tenant network intake/routing and reviewer
grants are not implemented**; do not claim that one operator can review every separately
registered tenant. A shared network workspace or a separately approved routing/grant design
is needed before public partner recruitment.

Lifecycle vocabulary:
APPLICATION, UNDER_REVIEW, VERIFICATION_REQUIRED, VERIFIED, AGREEMENT_PENDING, APPROVED,
INTEGRATION_TESTING, ACTIVE, SUSPENDED, REJECTED.

Operator confirmation and recorded evidence references gate manual verification, accepted
agreements and offline integration-test evidence. Information requests, rejection and suspension
need explanatory notes. Applicant edits invalidate review/approval and return to APPLICATION;
historical evidence/audits remain. Reopening suspension/rejection requires fresh review.
Stale versions are rejected, not silently overwritten. API callers cannot write statuses directly.

**VERIFIED** in this workflow means an explicitly authorized operator recorded a manual
review/attestation with an evidence reference. It is not independent government confirmation.
An agreement record is an operator attestation, not an e-signature provider integration.
Integration-test evidence is not a connected API. **ACTIVE is deliberately blocked in this
phase**; no operator button can activate an external action, paid service or actual access
credential. Suspension invalidates planning eligibility; no live partner credentials exist
here to revoke. Actual service delivery/access revocation remain future adapter work.

### Government resources and jurisdiction coverage

Official links cover SBA, IRS, USPTO, U.S. Copyright Office and FinCEN. Catalog classifications
distinguish official public information, verified API connections, restricted partner APIs,
authorized filing capabilities and manual verification requirements. Only public-information
references are actually supplied; none is promoted to a verified API or filing capability.

The catalog enumerates all 50 states plus Washington, DC and links to the official USA.gov
state/territory directory for authoritative discovery. **These are jurisdiction discovery
records, not 51 verified formation/licensing integrations.** County/municipal and additional
federal agencies remain manual-review adapter boundaries. Do not claim local coverage or
current agency requirements without separate source checking.

### Automation and promotion

The existing B.I.G. agent permission/planning module covers the requested Commander, Marketing,
Growth, Finance, Compliance, Operations and Security roles (plus the earlier planned roles).
All agents remain planned, with zero live spend and no autonomous external tools.
Durable queues, task dependencies, production workers and performance feeds remain planned.

Operators can prepare co-marketing drafts tied to a private partner application. Internal
approval requires an approved relationship and a recorded partner co-marketing permission
reference. Applicant edits, rejection, suspension and reopen invalidate approved promotion
plans back to draft in the same transaction. Approval is serialized with relationship changes.
Draft attribution codes prepare a future referral schema; **they are not public
tracking links** and collect no referrals. Archive preserves draft records.
No partner logo is copied, no advertisement is published, no commission is authorized, and
no performance/revenue figures are invented. Verified performance is explicitly unavailable.
Connected analytics, lawful referral arrangements and provider-confirmed attribution remain
future work, requiring authorization and appropriate privacy/contract review.

## Security, storage and compatibility

Additive migration chain: `g0001 → g0002 → g0003 → g0004 → g0005`.
`g0005` adds only `partner_applications` and `partner_promotions`; prior migrations are unchanged.
Downgrade refuses to delete populated partner tables. Existing customer/financial records
are not rewritten. Production migrations require explicit review and approval.

All mutations require authenticated sessions, CSRF, tenant checks and non-lockdown status.
Operator mutations additionally require explicit allowlist authorization and confirmation.
Server-owned identity, workflow state, timestamps, versions and attribution IDs are never
accepted as applicant facts. Strict input schemas reject unknown fields. Audit detail records
contain action, status and version, not contact, credential descriptions or free-text services.
Evidence references are private operator data and must not contain secrets or signed document URLs.

Shared production rate limits, human credential vetting policies, reviewer assignments,
retention/deletion, signed agreements, connected APIs, real performance monitoring, actual
partner delivery, production infrastructure and real-user accessibility studies remain release
requirements. No production-readiness claim is made.

## Verification and handoff

Automated tests cover default-deny access, tenant/applicant isolation, explicit consent,
validation, state injection, CSRF, lockdown, stale writes, evidence/agreements, approval
invalidation, suspension/reopen and internal promotion permission guards.
The final completion report records actual results, files, browser scope, source commit and
GitHub synchronization status. No paid provider, government filing or publishing is authorized.
