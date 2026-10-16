# B.I.G. Phase 2 — consolidated executive report

Authorization: Executive Order 002. External spending $0; paid AI, billing,
government submissions, public deployment and Phase 3 remain OFF.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| 1 Baseline preservation | IMPLEMENTED AND VERIFIED | 196 passed, 1 optional PostgreSQL skip; no failed tests. |
| 2 Intelligence foundation | IMPLEMENTED AND VERIFIED | 17 tests passed; zero failures. Mock only; live reasoning unverified. |
| 3 Intelligence-to-execution | IMPLEMENTED AND VERIFIED | 7 integration tests passed; frontend typecheck passed. Initial fixture import/session/setup errors repaired; no remaining failures. |
| 4 Financial protection | IMPLEMENTED AND VERIFIED, OFFLINE | 14 tests; atomic five-scope virtual reservations, uncertain holds and overrun shutdown. Paid transport hard-blocked. |
| 5 Economics and research | RESEARCHED ONLY; reproducible model IMPLEMENTED AND VERIFIED | Research gate passed: three provider configurations, 48 simulated customer cases, official competitor matrix and 3 model tests. Commercial prices remain hypotheses. |

## Baseline preservation

- Branch: `genesis-os-2-development`.
- Starting local/GitHub HEAD: `67ccd906d1a80479f3d0b40f96694e75d96e94b9`.
- Phase 1 commit `8c88c71048a8f829f984eb312a1825df85da0826` is preserved.
- Working tree initially contained only the newly supplied executive order.
- Root database: 18 tables / 0 rows. Backend: 36 tables / 154 rows.
- Read-only row snapshots and SQLite backup copies are retained in the excluded
  `generated-artifacts/phase2-preservation/` directory; no customer fixture is
  inserted into an original database. Tests use explicitly isolated databases.
- Reuse: Master Orchestrator actions/receipts, AutoForm and Passport consent,
  deterministic financial model and itemized plans, two-strategy recommendations,
  Executive Board, Founder DNA, Digital Twin, Mission Control, consultation,
  Partner Network, scoped ownership checks, CSRF, lockdown and audit events.
- Gates 1–4 passed in order. Gate 5 is research/model acceptance, not approval to
  charge customers or activate a live provider. The complete Phase 2 decision is
  conditional on final browser and source-control evidence below.

## Executive summary and delivered components

**IMPLEMENTED AND VERIFIED:** provider-independent structured intelligence
contracts, deterministic mock provider, persisted private proposal history and
provenance, hash/schema/financial/source validation, allowlisted internal tool
handoff, owner-only financial-control simulator, and consented funding
preparation/tracking. Master Orchestrator remains execution authority.

**IMPLEMENTED BUT NOT FULLY VERIFIED:** future OpenAI-compatible adapter boundary
and provider-independent interfaces. Live transport remains deliberately disabled;
these are not proof of live connectivity, latency, reasoning quality, production
underwriting or live bill reconciliation.

**RESEARCHED ONLY:** model/competitor rates, usage forecasts and membership/
fixed-service prices. **BLOCKED:** paid/live AI activation and consequential
external operations. **NOT STARTED:** Phase 3 and commercial rollout.

### Intelligence architecture and execution

- Strict contracts describe strategies, three financial plans, dependencies,
  regulatory references, risks, proposed tasks and supporting evidence. Arbitrary
  permissions, tools, verified claims and fabricated regulatory sources are
  rejected. Saved business idea, plan, strategy and consented Passport business
  name/municipality are reused; contact identity, credentials and immigration
  declarations are not supplied to the mock provider.
- Provider requests use bounded concurrency, timeouts and retry ceilings.
  Timeouts do not stack retries while the prior attempt is still running.
  Record status distinguishes a failed request from a valid proposal; failures
  leave existing deterministic Phase 1 tools available.
- Saved context/proposal hashes bind the handoff to the exact customer context.
  Applying a mock proposal cannot replace the customer's chosen strategy or
  plan, transfer document approval, sign, file, pay, or generate fictitious
  completion evidence. Actual server-owned internal tools generate receipts.
- Existing Executive Board, Founder DNA, Digital Twin, strategy/three-plan
  engine, Passport/AutoForm, Mission Control and scoped ownership checks are
  reused. Funding adds opt-in actions rather than changing the original
  thirteen-action Phase 1 roadmap for everyone.

### Security, privacy and financial controls

- Tests exercise CSRF, sign-in/resume, same-tenant and cross-tenant ownership,
  owner/customer role separation, malicious tools, output/hash tampering,
  missing authorization, exact revisions, idempotency and concurrency.
  This is application regression evidence, not an external penetration test.
- The funding form rejects undeclared fields (including SSN/passport-number
  fields) and never requests immigration documents, credit reports or criminal
  history. Free-text fields still require customers not to include sensitive
  identity numbers; automated PII detection is NOT implemented.
- New records are additive and private. Source snapshots and packets are
  immutable by revision; approvals bind the exact content hash. Changed packets
  require new approval and reset the Mission Control review task. Customer-
  reported funding outcomes are explicitly unverified, never funding evidence.
- Owner financial policy defaults to emergency shutdown, simulated usage OFF
  and every authorization amount zero. The owner can configure only offline
  simulation, not activate paid AI. A separate server hard ceiling is $0
  regardless of credentials, environment flags or policy edits.
- Virtual accounting uses integer micro-USD, maximum preauthorization and atomic
  request/task/customer/day/month limits, a model allowlist, bounded concurrency
  and retries, persisted idempotency and audits. Interrupted/unknown usage stays
  reserved until verified reconciliation; reservations never expire into free
  budget. Overruns trigger shutdown. The test tariff ($1/M input, $4/M output)
  is explicitly fictional and distinct from the official research below.
- Real provider billing delays, model-price changes, regional premiums,
  cache charges and uncertain interrupted usage remain future exposure. No
  software reservation proves a provider's final bill or makes live use free.

## Directive 002-A — mandatory capability ledger

Statuses in this section use the directive's exact vocabulary. No external
blocker removes the corresponding mandatory requirement.

| Capability | Status | Actual evidence / remaining requirement |
|---|---|---|
| Analyze saved financing needs | IMPLEMENTED AND TESTED | Selected itemized plan and funding gap reused; requested amount/use saved once. Input economics remain unverified customer estimates. |
| Citizenship/immigrant/visa-holder journeys | IMPLEMENTED AND TESTED | Separate optional circumstance and work-authorization declarations, distinct ownership/licensing/funding notices, USCIS reference and professional escalation. Visa-holder and permanent-resident tests pass. No individualized legal determination. |
| Structured private funding records | IMPLEMENTED AND TESTED | Consented, versioned profiles and immutable hashed internal preparation packets; additive migration. |
| Grant/loan published-criteria screening | IMPLEMENTED AND TESTED | Named SBA Microloan, Kiva U.S. and Amber Grant sources; positive, ineligible and uncertain cases. Preliminary matches are never certified eligibility. |
| Federal/state/local grant discovery | PARTIALLY IMPLEMENTED | Source-reviewed Grants.gov and New York ESD discovery directories, clearly NOT actual award offers. Current open notices, notice-specific matching and other states/localities remain mandatory work. |
| Private/nonprofit grants | PARTIALLY IMPLEMENTED | Amber Grant is an actual named private program; published criteria/fee/deadline rule shown. Live cycle, award amount inconsistencies and broader nonprofit grant coverage still require verification. Kiva is labeled a LOAN, not a grant. |
| SBA-supported financing/microloans | PARTIALLY IMPLEMENTED | Source-backed screening and internal packets; the March 9, 2026 SBA citizenship restriction is not replaced with older permanent-resident eligibility assumptions. Current intermediary requirements/offers must be verified. |
| CDFIs/community lenders/credit unions | PARTIALLY IMPLEMENTED | Official Treasury CDFI and NCUA directories; not offers. Named lender products, membership, eligibility and verified term sheets remain mandatory work. |
| Explain restrictions/missing information | IMPLEMENTED AND TESTED | Requirements, unknown declarations, source date, current-status caveat, application-information checklist and professional-review escalation in UI/records. |
| Loan comparison/affordability | IMPLEMENTED AND TESTED | Cent-accurate amortization, zero-interest handling, final-payoff reconciliation, fees, net proceeds and plan-cashflow comparison; up to three saved comparisons resume. Quotes are customer-supplied, not verified APR/underwriting. |
| Automatic supported preparation | IMPLEMENTED AND TESTED | Consent + saved Passport automatically create supported Kiva/Amber/SBA internal packets when screening permits; missing Passport business name pauses until supplied, then resumes. These are JSON preparation worksheets, NOT official program forms. |
| Official application forms/provider-specific documents | BLOCKED BY EXTERNAL DEPENDENCY | Approved/current form specifications, provider authentication/integrations and legal/provider review unavailable. Must not advertise current worksheets as filed applications. |
| Exact-revision customer approval | IMPLEMENTED AND TESTED | Current hash/revision required; stale/tampered packet rejected; approval is internal preparation ONLY. |
| Orchestrator/AutoForm/Passport/Mission Control integration | IMPLEMENTED AND TESTED | Existing actions, dependencies, internal receipts, Passport reuse and review tasks; revised packet review resets. Actual lender completion is never fabricated. |
| Deadlines, outcome tracking and resume | IMPLEMENTED AND TESTED | Source deadline rules plus separately labeled customer-tracked dates and unverified customer-reported outcomes; same-account persistence and duplicate suppression. Live deadline monitoring/notifications are not implemented. |
| Actual applications, credit checks, document transmission | BLOCKED BY EXTERNAL DEPENDENCY | No approved integration, consequential authorization or current execution permission. No submission route exists; status remains BLOCKED_NO_APPROVED_INTEGRATION. |
| Broad multi-jurisdiction live discovery and specialized immigration casework | NOT IMPLEMENTED | Mandatory retained scope. Requires source adapters, verified current forms and qualified professional escalation pathways, not more generic informational pages. |

### Funding source register

All sources below accessed **2026-10-16 UTC (2026-10-15 America/New_York)**.
Source review is not proof that an application is currently open. Records have
requirements, verification date, source, missing inputs, application requirements,
deadline rule and `LIVE_APPLICATION_AVAILABILITY_UNVERIFIED` status. After 30 days
the snapshot becomes stale and preparation/approval blocks pending re-verification.

| Source | Supported fact / boundary |
|---|---|
| [USCIS entrepreneur pathways](https://www.uscis.gov/working-in-the-united-states/entrepreneur-employment-pathways/immigrant-pathways-for-entrepreneur-employment-in-the-united-states) | Ownership does not itself grant permission to work; individualized legal questions escalate to qualified professionals. |
| [SBA Microloans](https://www.sba.gov/loans/microloans/) and [SBA March 9, 2026 citizenship notice](https://www.sba.gov/article/2026/03/09/sba-bans-foreign-nationals-accessing-sba-backed-loans) | Published ownership/principal-residence restriction; do not assume permanent residents/visa holders qualify. Intermediary review still required. |
| [Kiva U.S.](https://www.kiva.org/borrow) | Published 0% interest, no fees/collateral/minimum score; applicant 18+, U.S. residence/operations, Nevada/North Dakota exclusions and additional provider criteria. Social fundraising is required, not guaranteed funding. Sensitive provider checks remain outside B.I.G. |
| [Amber Grant FAQ](https://ambergrantsforwomen.com/faq/) | Woman applicant 18+, at least 50% women-owned U.S./Canada business; $15 fee and possible waiver; month-end Eastern deadline rule. FAQ contains conflicting award amounts, so no guaranteed dollar amount is quoted. No fee paid. |
| [Federal search](https://simpler.grants.gov/search) | Directory, not a specific eligible award. |
| [New York ESD](https://esd.ny.gov/doing-business-ny/small-business-hub) | State/local financing and immigrant entrepreneur resources; program-specific verification required. |
| [Treasury CDFI awards](https://www.cdfifund.gov/awards/state-awards) | Organizations, not business loan offers. |
| [NCUA locator](https://mapping.ncua.gov/) | Credit union listings, not membership or lending approval. |

## Milestone 5 — AI provider economics

**RESEARCHED ONLY.** Official USD token prices per million, accessed
2026-10-16 UTC. These configuration labels are cost/suitability hypotheses,
not measured capability rankings. No live provider was called or activated.

| Configuration | Provider/model | Input | Cached input | Output | Other published cache costs |
|---|---|---:|---:|---:|---|
| Economy-first | OpenAI gpt-6-luna, standard short context | $0.10 | $0.01 | $0.50 | Cache writes $0.125/M |
| Balanced | Google Gemini 3.1 Flash-Lite, standard text | $0.25 | $0.025 | $1.50 | Cached-token storage $1/M/hour; creation modeled at standard input rate |
| Advanced reasoning hypothesis | Anthropic Claude Opus 5.5 | $4.00 | $0.20 | $20.00 | 5-minute writes $5/M; published 1-hour writes $8/M (model uses 5-minute rate) |

Sources: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing),
[Google API pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
OpenAI's marketing `/api/pricing` redirect showed ChatGPT seat pricing and was
explicitly NOT used as API pricing.

### Transparent workflow model

- Per completed workflow: 15,000 input tokens; 5,000 output tokens; 25% cached
  input; 1.2 full billable attempts; 95% success rate. Conservative repeated
  cache creation is added per attempt; Google's one-hour cache storage is also
  charged. These are simulated assumptions, not observed customer usage.
- Successful inference cost = (uncached input + cached reads + output +
  cache creation + applicable storage) × 1.2 / 0.95.
- Add **assumed** $0.01 internal tool execution + $0.005 internal document
  compute per completed workflow. These are not vendor quotes. External
  search, OCR, PDF extraction, financial-data APIs, provider tools, storage
  beyond the stated cache, regional premiums and professional work are
  excluded and must be quoted before activation.
- Estimated successful workflow: **economy $0.020218**, **balanced $0.034066**,
  **advanced $0.222789**, including those assumed tool/document costs.
  Actual measured live AI cost: **unavailable**, not zero-cost evidence.
  Actual authorized external spending in this phase: **$0**.
- Latency and live structured-output reliability: **UNVERIFIED for all three**.
  The offline mock validates the parser/controller, not vendor quality.
  Future benchmark: blinded cleaning/bakery/consulting/funding scenarios,
  schema acceptance, factual/source errors, revision consistency, success/
  retry rate, p50/p95 latency and provider-billed cost per successful workflow.
- Prefer deterministic software for money, amortization, thresholds, eligibility
  screens, permissions, hashes, state transitions, idempotency and receipts.
  Use a future evaluated model for language/context interpretation only within
  validated contracts; higher model cost does not establish legal accuracy.

Reproduce the complete 48-case model:

```sh
cd genesis-business-os/backend
python -m app.services.unit_economics
python -m pytest tests/test_unit_economics.py -q
```

## Milestone 5 — official competitor matrix

**RESEARCHED ONLY.** Access date for EVERY row: **2026-10-16 UTC**. USD;
state/government fees are additional and jurisdiction-dependent. “Not verified”
means the reviewed official material did not establish an exact comparable
price/term, NOT that the competitor does not offer the service. No universal
cheapest claim is justified.

Official sources:
[Z1 formation](https://www.zenbusiness.com/pricing-formation-plans/),
[Z2 registered agent](https://www.zenbusiness.com/registered-agent-service/),
[Z3 service catalog](https://www.zenbusiness.com/);
[L1 formation](https://www.legalzoom.com/),
[L2 agent](https://www.legalzoom.com/business/business-operations/registered-agent-overview.html);
[B1 formation](https://bizee.com/),
[B2 professional-partner terms](https://bizee.com/company/bizee-pro-suite);
[T1 pricing](https://www.tailorbrands.com/pricing),
[T2 agent](https://www.tailorbrands.com/llc-formation/registered-agent).

| Provider / service | Published price & period | Included scope | Exclusions / renewal / qualification | Source |
|---|---|---|---|---|
| ZenBusiness formation | Starter $0 one-time; Pro $199/yr; Premium $299/yr | State formation package; upgraded features depend on tier | State fees extra; Starter does not renew, Pro/Premium renew $199/$299 annually | Z1 |
| ZenBusiness registered agent | Advertised $99 first year, $199/yr thereafter | Registered-agent service | Page advertises first-year discount when forming an LLC; verify qualification. Introductory price is not standard renewal; state fees extra | Z2 |
| ZenBusiness business planning | Not verified as standalone comparable price | Reviewed formation/support packages | Do not equate filing assistance with a B.I.G. financial plan | Z1, Z3 |
| ZenBusiness document preparation | Tier-dependent; standalone price not verified | Formation documents; package features vary | Legal advice/custom document equivalence not established | Z1 |
| ZenBusiness licensing assistance | Not verified | Availability/catalog description only | Actual license filings/government fees not established | Z3 |
| ZenBusiness compliance | Worry-Free Compliance listed $199/yr; Advanced listed $299/yr | State-report/compliance support according to selected product | Government fees and exact add-on terms must be checked; avoid double-counting bundled coverage | Z1, Z3 |
| ZenBusiness subscriptions | Pro $199/yr; Premium $299/yr | Tier's recurring package features | Not monthly formation fees; separate agent/add-ons may recur | Z1 |
| ZenBusiness renewal charges | Pro $199/yr, Premium $299/yr, agent $199/yr after first year | Continuation of chosen services | Cancellation and current checkout terms require verification | Z1, Z2 |
| ZenBusiness government fees | Variable; excluded | None assumed in $0 offer | State filing/license/report fees are not B.I.G. membership revenue | Z1 |
| ZenBusiness optional add-ons | Product-specific; not all prices verified | Agent/compliance and other catalog services | No assumed all-inclusive bundle | Z3 |
| LegalZoom formation | $0 basic; $249 Managed; $299 Expert headline packages | Formation essentials; higher packages add advisory/professional services | State fees extra; no assumption all support is perpetually included | L1 |
| LegalZoom registered agent | $249/yr | Agent service per product page | Separate from state filing fees and most headline formation prices | L2 |
| LegalZoom business planning | Standalone comparable plan price not verified | Managed business-advisor support listed | Advisory scope differs from deterministic B.I.G. worksheets | L1 |
| LegalZoom document preparation | Package-specific; separate equivalent price not verified | Formation documents; operating agreement in described upgraded scope | Custom legal work/external professional service not equivalent to a JSON worksheet | L1 |
| LegalZoom licensing assistance | Not verified | No separately priced equivalent established | License/government fees extra; do not invent an add-on price | L1 |
| LegalZoom compliance support | Dedicated-advisor trial in described package; $49/mo auto-renew after included 30 days | Setup/compliance/coaching support as described | Trial/renewal must be separated from one-time filing; tax/accounting offers may have separate trials | L1 |
| LegalZoom subscriptions | $49/mo advisor continuation in reviewed offer | Continuing advisor access for that offer | This is not all-inclusive platform/attorney pricing | L1 |
| LegalZoom renewal charges | Agent $249/yr; described advisor $49/mo after 30 days | Selected recurring services | Other renewals not verified; cancel per terms | L1, L2 |
| LegalZoom government fees | Variable; excluded | No fixed nationwide amount assumed | State fees additional | L1 |
| LegalZoom optional add-ons | Tier-specific; standalone prices not all verified | Expert package advertises professional team | Do not treat formation package price as unlimited ongoing legal work | L1 |
| Bizee formation | Basic $0, Standard $199, Premium $299; one-time | Formation package; first registered-agent year included | State fees extra; paid package features vary | B1 |
| Bizee registered agent | First year included with formation; consumer renewal NOT verified | First-year service | $119/yr is verified ONLY in professional-partner Bizee Pro terms; not generalized to direct consumers | B1, B2 |
| Bizee business planning | Standalone comparable price not verified | No equivalent full planning service established | No assumed equivalence with strategy/financial forecasts | B1 |
| Bizee document preparation | Package-dependent; standalone price not verified | Formation paperwork; extra package documents vary | Custom legal equivalence not established | B1 |
| Bizee licensing assistance | Exact comparable price not verified | Research/catalog coverage not enough for a fixed quote | Filing and government fees not assumed included | B1 |
| Bizee compliance | Exact recurring product price not verified | Described reminders/formation support | Professional-partner reminder tools are not proof of all consumer compliance filings | B1, B2 |
| Bizee subscriptions | Formation packages are one-time; other subscriptions not fully verified | Professional-partner program has no membership fee | Partner $99 + state fee formation offer is a different channel, not a consumer comparison | B1, B2 |
| Bizee renewal charges | Consumer agent renewal not verified; partner-channel $119/yr after year one | Only stated channel's service | Never label introductory included year a free lifetime agent | B1, B2 |
| Bizee government fees | Variable; excluded | None assumed | State fees additional | B1 |
| Bizee optional add-ons | Package/channel-specific; exact full list not verified | Paid formation tiers add services | Verify selected checkout, recurring offers and exclusions | B1 |
| Tailor Brands formation | Lite $0; Essential $199/yr; Elite $249/yr | LLC formation; annual tiers add compliance/branding/tools according to plan | State fees extra; Lite is not proof of free agent or all compliance work | T1 |
| Tailor Brands registered agent | Vendor's exact price not verified | Product page describes agent handling/scanning/notices | Generic market ranges $99–$300/$50–$300 are NOT a Tailor Brands quote | T2 |
| Tailor Brands business planning | Coaching/funding search described in paid annual plans | Business/coaching educational tools | Not verified equivalent to financial plan/immigration/funding execution | T1 |
| Tailor Brands document preparation | Tier-specific; standalone price not verified | Operating agreement described in Essential/Elite scope | No claim of custom legal service equivalence | T1 |
| Tailor Brands licensing assistance | Exact equivalent price not verified | Product/package-specific | Government/license costs not established | T1 |
| Tailor Brands compliance | Described in $199/$249 annual tiers | Annual compliance/report update scope in paid tiers | State fees/eligibility/add-on terms still apply | T1 |
| Tailor Brands subscriptions | Essential $199/yr; Elite $249/yr | Selected annual package | Bookkeeping trial is 30 days, not free ongoing service | T1 |
| Tailor Brands renewal charges | Annual price advertised; separate promotional renewal schedule not verified | Continuing annual services per current terms | Domain/bookkeeping/agent renewals require checkout-specific confirmation | T1 |
| Tailor Brands government fees | Variable; excluded | None assumed | State fees additional | T1 |
| Tailor Brands optional add-ons | Agent, bookkeeping/domain extras not fully priced in reviewed material | Paid tiers vary; Elite includes additional branding tools | No invented exact price or all-inclusive promise | T1, T2 |

B.I.G.'s present private planning/worksheet output is **not equivalent to actual
state filing, registered-agent representation, licensed legal advice or lender
underwriting**. Formation advertised at $0 also prevents any honest claim that
a paid B.I.G. membership is universally the cheapest formation service.

## Milestone 5 — B.I.G. pricing and unit economics

**RESEARCHED ONLY; no billing activation or commercial-price approval.**
Evaluate DISCOVER $0, START $9.99/month, BUILD $19.99/month, OPERATE $39.99/month.

Assumptions: light 2, typical 10, heavy 100, extreme 2,000 successful workflows/
customer/month; variable support 0.5/3/12/60 minutes respectively at assumed
$30/hour; $0.20 variable infrastructure/customer; $50 fixed opex/month divided
among 100 active customers; $30 CAC amortized over six paid months = $5/customer/
month. These are hypotheses, not actual Replit bills, actual CAC or measured
retention. DISCOVER has no paid AI but incurs modeled infrastructure/support.

Payment assumptions from [Stripe U.S. pricing](https://stripe.com/pricing)
and [Billing pricing](https://stripe.com/billing/pricing), accessed 2026-10-16:
2.9% + $0.30 domestic card charge; 0.7% subscription billing. These are research
inputs only: existing Square is preserved, Stripe is not connected, fees and
jurisdiction must be confirmed for the eventual authorized provider. Assume
2% revenue refund reserve, 0.5% revenue dispute reserve + $0.015/paid customer
(0.1% assumed incidence × researched $15 dispute charge). Actual disputes,
refund policy and unrecovered processing fees can differ materially.

**Definitions:** gross revenue − variable delivery cost = contribution margin;
subtract allocated fixed opex and separately allocated CAC to estimate operating
profit **before income tax**. Neither contribution margin nor that forecast is
verified net profit. Government fees, professional legal/provider work, owner
salary, unpriced integrations and financing costs require separate decisions.

Balanced-configuration illustration, USD/month, rounded for display. The
reproducible model includes every component and all 48 tier/usage/config cases.

| Tier | Usage | Gross revenue | Variable cost | Contribution margin | Fixed opex | CAC | Est. operating profit before tax |
|---|---|---:|---:|---:|---:|---:|---:|
| DISCOVER | Light | 0.00 | 0.45 | -0.45 | 0.50 | 5.00 | -5.95 |
| DISCOVER | Typical | 0.00 | 1.70 | -1.70 | 0.50 | 5.00 | -7.20 |
| DISCOVER | Heavy | 0.00 | 6.20 | -6.20 | 0.50 | 5.00 | -11.70 |
| DISCOVER | Extreme | 0.00 | 30.20 | -30.20 | 0.50 | 5.00 | -35.70 |
| START | Light | 9.99 | 1.44 | 8.55 | 0.50 | 5.00 | 3.05 |
| START | Typical | 9.99 | 2.97 | 7.02 | 0.50 | 5.00 | 1.52 |
| START | Heavy | 9.99 | 10.53 | -0.54 | 0.50 | 5.00 | -6.04 |
| START | Extreme | 9.99 | 99.26 | -89.27 | 0.50 | 5.00 | -94.77 |
| BUILD | Light | 19.99 | 2.05 | 17.94 | 0.50 | 5.00 | 12.44 |
| BUILD | Typical | 19.99 | 3.58 | 16.41 | 0.50 | 5.00 | 10.91 |
| BUILD | Heavy | 19.99 | 11.14 | 8.85 | 0.50 | 5.00 | 3.35 |
| BUILD | Extreme | 19.99 | 99.87 | -79.88 | 0.50 | 5.00 | -85.38 |
| OPERATE | Light | 39.99 | 3.27 | 36.72 | 0.50 | 5.00 | 31.22 |
| OPERATE | Typical | 39.99 | 4.80 | 35.19 | 0.50 | 5.00 | 29.69 |
| OPERATE | Heavy | 39.99 | 12.36 | 27.63 | 0.50 | 5.00 | 22.13 |
| OPERATE | Extreme | 39.99 | 101.09 | -61.10 | 0.50 | 5.00 | -66.60 |

### Conditional recommendations, not offers

- **DISCOVER free:** deterministic self-service preview only, zero paid AI
  allowance, no included human work. Modeled cost makes it an acquisition
  subsidy, not a profitable standalone service. Bound abuse and acquisition
  spend explicitly rather than hiding that loss.
- **START $9.99:** capped pilot hypothesis, 10 economy workflows/month and
  maximum $0.50 monthly AI authorization per customer, subject to future
  owner-approved global budgets. Typical balanced scenario has only $1.52
  estimated operating profit. Its conditional break-even price is about
  $8.37 under these assumptions; that is not a validated sustainable market
  floor. Heavy usage or higher CAC/support makes $9.99 unsustainable.
- **BUILD $19.99:** hypothesis with 30 economy/balanced workflows/month and
  proposed $1.50 customer AI ceiling; no advanced-model entitlement.
- **OPERATE $39.99:** hypothesis with 80 bounded economy/balanced workflows,
  at most four advanced escalations and proposed $4 customer AI ceiling.
  Limits/allowances above are RECOMMENDATIONS, not enabled entitlements.
- Typical-support contribution break-even usage for the balanced model is
  approximately START **216**, BUILD **491**, OPERATE **1,043** workflows,
  BEFORE fixed costs/CAC and assuming support does not grow. With heavy support,
  START breaks even at only **84**. These are risk thresholds, NOT safe included
  allowances. All paid tiers lose money at the extreme modeled usage; never
  promise unlimited advanced reasoning, tools or professional work.
- Optional **$4.99 internal worksheet packet** hypothesis: at most three balanced
  workflows and one support minute. Under the same one-off card/refund/dispute/
  infrastructure assumptions (no subscription fee), estimated contribution is
  about $3.60, before fixed costs/CAC/tax.
- Optional future **$14.99 bounded advanced-review bundle** hypothesis: at most
  three advanced workflows and six support minutes, estimated contribution
  about $10.00 before fixed costs/CAC/tax. It is BLOCKED from sale until live
  quality, authorization, delivery and provider billing are verified. Neither
  price covers official filing, application fees, legal advice or guaranteed funding.
- No unconditional “lowest sustainable price” is established: willingness to
  pay, live quality, support, retention, taxes, infrastructure and real CAC
  require measured pilot evidence and an explicit owner decision.

## Final regression, browser acceptance and preservation

Backend final verification: **248 passed, zero failed, zero skipped** including
the original Phase 1 tests, 17 intelligence-foundation cases, 7 execution cases,
14 financial-control cases, 10 funding cases and 3 economics cases. SQLite and
explicitly local disposable UTF-8 PostgreSQL upgrades preserve original rows,
document source/hash and approvals through `g0011`; Alembic schema check passes.
Non-failing warnings concern Starlette TestClient/httpx, argon2 version access
and Alembic path separator defaults; they are disclosed, not hidden failures.

Frontend TypeScript and production build pass. A first shell build lacked the
required PORT variable and stopped in configuration; the correctly configured
`PORT=5173 BASE_PATH=/ pnpm --filter @workspace/genesis-app build` passes.
Initial milestone test-fixture errors were corrected and are not hidden as
successful first attempts.

After conservative cache-write/storage charges were added, one economics test
incorrectly assumed caching must always save money: that run was 246 passed /
1 failed. The assertion was corrected to reflect the model's full cache cost,
not by removing cache charges. Repeated cache creation can cost more than
uncached inference; cheap cache-read prices alone are insufficient evidence.

The first browser attempt stopped at a collapsed proposal; its backend record
was valid. The latest proposal now opens automatically with an explicit review
label. Packet JSON wraps on narrow screens. The same tester continued the
unfinished checks (not a second independent test run) and returned **success**.
One final guard prevents an uninitialized legacy project from acquiring only a
partial funding roadmap; all **10 affected funding tests passed** after that
guard, in addition to the full 248-test run.

### Actual desktop and signed-in mobile acceptance

- Desktop: saved idea → same Business Project → mock proposal review/apply
  succeeds. Selected Focused recurring-client strategy and Build Strong plan
  remain unchanged. Exactly one applied proposal/receipt after refresh/resume.
- Visa-holder funding declarations saved once with consent. SBA screening
  returns ineligible for the declared ownership condition; Kiva/Amber are
  preliminary, not certified. Four resource entries are labeled directories.
  The requested funding amount correctly reused the saved $3,420 plan gap,
  distinct from the customer's original $3,000 available capital.
- Two integrity-verified revision-one internal packets were prepared. Kiva
  exact-hash internal approval persists; Amber remains awaiting review. A
  deliberately customer-tracked test date of 2026-12-31 persists with
  NOT_SUBMITTED; this is not asserted as Kiva's official deadline.
- The independently entered $3,000/0%/36-month loan scenario pays $83.33 for
  months 1–35 and $83.45 in month 36; $3,000 total, zero interest. Disclaimer,
  payoff schedule and comparison persist after logout/login.
- Signed-in mobile at 390×844 resumes the same account/project without re-entry;
  counts remain one proposal, two packets, one comparison. Root/body
  scrollWidth 375 equals clientWidth 375: no page-level horizontal overflow,
  including an expanded loan schedule.
- Owner controls at `/next/owner/`: paid AI OFF, $0 authorization, emergency
  shutdown ON, simulation unchecked, every limit zero, virtual tests disabled.
  No setting was enabled. Zero signatures, submissions or financial policies
  existed in the isolated database at final inspection.
- Evidence screenshots: `3lgptg` (desktop applied mock), `e3535i` (Kiva
  restrictions), `8y9hzu` (Kiva internal packet), `xc7i4q` (Amber review),
  `6t565b` (mobile loan), `xtx2r7` (mobile same-account resume),
  `csjfti` (owner financial shutdown).
- Non-blocking observations disclosed: one unauthenticated resource 401 logged
  during each successful sign-in; the Owner console link could not be activated
  by the test click, so the tester used its observed `/next/owner/` href directly.
  The pre-existing native:sources action showed FAILED in the deliberately
  offline QA fixture and was not retried. These do not establish live-source
  validation or genuine AI quality and are not silently reported as fixed.

Browser QA uses a **reconstructed equivalent**, isolated saved New York cleaning/
$3,000 scenario. The prior Phase 1 QA identity was deleted after acceptance;
this is not a claim that the identical original QA account was resumed.
The original root/backend customer databases are never the QA target.

### Final preservation and restoration proof

- Original root: **18 tables / 0 rows**, every original row set unchanged.
- Original backend: **36 original tables / 154 original rows**, every original
  row set unchanged. Six additive Phase 2 tables exist empty; none contains QA
  profiles, intelligence, applications, cost policies, buckets or reservations.
- Both original databases return `PRAGMA integrity_check = ok` and no
  foreign-key-check violations. Existing document source/hash/approval
  preservation is additionally tested through SQLite/PostgreSQL upgrades.
- Disposable browser SQLite, its temporary identity metadata and the stopped
  local PostgreSQL cluster were removed. Only QA-created data was deleted;
  original recoverable backups and excluded verification logs were retained.
- Temporary database/owner-allowlist environment values were removed and the
  full original `.replit` configuration restored byte-for-byte. The managed API
  was restarted against its original development database. Production settings,
  customer billing/payment connections and protected main were not modified.

## Remaining mandatory work and activation prerequisites

1. Approve whether/when a real model may be evaluated, with nonzero explicit
   spending limits. Select an approved provider integration and privacy/
   retention/data-processing terms. Do not ask for or store credentials in chat.
2. Add reviewed live transport behind the validated adapter AND enforce the
   verified financial reservation/reconciliation path before every attempt.
   Confirm token ceilings, cache/tool/storage tariffs, provider-side account
   limits and uncertain-charge reconciliation. Independent live billing
   reliability and interruption/overrun tests remain mandatory.
3. Benchmark genuine reasoning, schema reliability, sources and latency against
   deterministic baselines. Mock results do not authorize a quality claim.
4. Implement current, source-specific funding-notice/lender-product discovery
   (especially federal/state/local and community/credit-union programs), current
   official form adapters, deadline monitoring and professional referral paths.
   Keep unavailable external steps mandatory, visibly blocked and unadvertised
   as active. Re-verify program sources after the snapshot's 30-day freshness
   window; no automated source re-verification is claimed.
5. Before actual applications/credit checks/document transfer, obtain separate
   exact customer authorization, approved integrations, provider/legal review
   and revised execution permission. Internal packet approval is insufficient.
6. Validate pricing with bounded measured pilot usage, support/CAC/retention,
   refund/dispute economics and like-for-like service scope. Any billing,
   payment-provider connection, spending, publishing or Phase 3 needs a separate
   executive decision.

**Phase 2 is not represented as unconditional live-service acceptance.**
The offline implementation/research gates can pass while mandatory live
funding coverage, official forms and genuine AI quality remain partial/blocked.
No paid AI, customer billing, real funding application, government submission,
public deployment, protected-main modification or Phase 3 is authorized.

## Source-control receipt

All verified work belongs on `genesis-os-2-development` only. The final exact
development commit, local/GitHub HEAD, ahead/behind and clean working-tree check
are appended to the delivered standalone copy after the normal fast-forward
push, avoiding an impossible self-referencing Git commit hash in its own file.
If GitHub moves or a safe fast-forward is unavailable, stop and report rather
than force-push or change credentials.
