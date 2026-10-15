# Genesis OnePay — payment recommendation and execution contract

## Status and recommendation

This is an architecture decision proposal, not an implemented checkout.
No Stripe account was connected, payment products created, customer charged, provider
paid or existing Square integration replaced.

**Recommend Stripe Connect as the primary future multi-provider marketplace adapter,
while preserving the existing Square adapter for authorized existing workflows.**
Approval is needed before connecting or implementing the selected payment arrangement.

Stripe Connect better matches the requested combined provider onboarding, payment
routing, payout management, recurring billing, refunds/disputes and platform reporting.
Square remains a viable seller-centric option; it is not dismissed as incapable of
marketplace fees. Provider eligibility, countries, contracts, actual pricing and
liability arrangements must be reviewed before selecting the final account configuration.

## Official-source comparison

| Requirement | Stripe Connect | Existing Square direction |
| --- | --- | --- |
| Provider onboarding | Hosted/embedded connected-account onboarding and capability requirements | Sellers authorize the platform through Square OAuth; permissions are required before acting for them |
| Platform fees | Connect application fees; funds flow depends on charge type | `app_fee_money` and `app_fee_allocations`; current documentation supports the seller, developer and one additional recipient |
| Multiple providers in one order | Separate charges/transfers can route a charge to multiple connected accounts, with platform fees/liability and eligibility implications | Application-fee allocations are not a general arbitrary-provider payout system |
| Provider payouts | Connect supports payout workflows subject to configuration, country and approved capabilities | The public Payouts API lists/gets seller payouts and entries; it is not an arbitrary provider-payout initiation API |
| Refunds/disputes | Charge type and account configuration determine affected balances, fees and loss liability | Existing payment/refund/dispute APIs must operate in the correct seller context and handle application-fee consequences |
| Subscriptions | Stripe Billing alongside the appropriate Connect account arrangement | Square has subscription capabilities; existing seller/payment compatibility must be verified |
| Genesis migration risk | New integration, account/capability setup, webhooks and accounting reconciliation required | Preserve current adapter and history; validate actual authorization before claiming operation |

The existing Square adapter's presence does not establish that OAuth marketplace fees,
subscriptions, payouts or disputes are already implemented or authorized.

## Funds-flow decision

1. Identify the actual seller/merchant and contractual responsibility for each service.
2. For Genesis-branded services delivered through approved providers, evaluate
   destination charges: Stripe documents them as a branded marketplace pattern.
   Stripe debits platform balances for relevant fees/refunds/chargebacks; contracts,
   loss responsibility and reserves need explicit review.
3. Where providers transact directly with customers, evaluate direct charges and
   current compatible connected-account configurations. Do not blindly combine direct
   charges with legacy Express/Custom accounts: current Stripe documentation cautions
   against that arrangement and points to compatible newer configurations.
4. Evaluate separate charges/transfers only when approved multi-provider routing is
   genuinely needed. It increases reconciliation and liability requirements.
5. OnePay is one coherent customer experience, not a promise that every provider,
   professional or government authority can participate in a single card charge.
   If separate merchants/charges are required, disclose and obtain consent for each.

Do not build an independent Genesis wallet, advertise escrow, hold/transmit funds
outside authorized provider arrangements or assume every connected provider is eligible.
Government-fee payment must use an authorized filing provider or supported official
payment path. No universal 50-state government-payment API has been verified.

## Checkout, data and authorization

- Use provider-hosted/tokenized payment components. Never store raw PAN, CVV or bank
  credentials in Genesis. Store only necessary provider IDs and minimized metadata.
- Quotes must itemize Genesis fees, provider fees, actual/estimated government fees,
  permitted commissions and applicable taxes separately. Include currency, seller,
  quote version/expiry, refund rules and customer consent before charging.
- Provider KYC/onboarding and bank collection remain in approved provider-hosted or
  embedded flows; verify capabilities before taking payments on their behalf.
- Existing customer identity, businesses and tenant ownership remain authoritative.
  Do not replace the FastAPI application, existing users or database to follow an SDK template.
- Payment-provider objects/prices remain canonical in the selected provider integration;
  application orders store provider references, accepted quote snapshots and fulfillment
  context, not a competing fake payment catalog.
- SDK/connector setup, test-mode validation and any webhook bridge must be reviewed
  against the current Replit integration and existing architecture before installation.
- Live transactions, refunds and payouts require explicit approval; do not infer it
  from an internal campaign approval or a planned marketing budget.

## Payment state is separate from service state

Payment lifecycle: awaiting authorization, processing, paid, failed, partially refunded,
refunded or disputed. Derive it from verified provider evidence, not a success URL.

Purchased-service lifecycle required by the complete directive:

| State | Required evidence / guard |
| --- | --- |
| PAID | Verified successful payment linked to the correct accepted quote and service |
| ASSIGNED | Approved provider assignment acknowledged and recorded |
| IN PROGRESS | Actual provider/workflow activity, not merely payment success |
| SUBMITTED | Submission acknowledgment/reference from the appropriate authority/provider |
| COMPLETED | Reliable completion confirmation; filing/payment success alone is insufficient |
| ACTION REQUIRED / VERIFICATION PENDING | Explicit customer/provider action with reason and next step |
| SUBMISSION FAILED | Recorded failure and safe retry/review path |
| CANCELLED / REFUND PENDING / REFUNDED / DISPUTED | Appropriate operational/payment evidence and reconciliation; refund does not erase a completed government filing |

The current preliminary journey's `PREPARED` and unstarted checklist steps are not
purchased services and must not be relabelled PAID, SUBMITTED or COMPLETED.

## Reliability and owner controls

- Verify webhook signatures on raw request bodies; validate expected merchant/account,
  event identity, currency/amount and relevant current provider status.
- Deduplicate provider events, persist idempotency keys, and handle retries/out-of-order
  delivery without duplicate charges, transfers, refunds or service submissions.
- Keep audit and reconciliation records. Distinguish gross receipts, taxes/government
  fees, provider liabilities, Genesis revenue, commissions, refunds and disputes.
- Price/commission edits need versioned authorization. Regulated professional referral
  arrangements require legal review; do not assume percentage fees are lawful.
- The full owner console still needs customer/provider/service/pricing/subscription/
  payment/refund/security/revenue controls. Current campaign planning is only one module.

## Indicative costs and approval gates

Stripe's reviewed US-facing Connect pricing page distinguishes pricing models:
“Stripe handles pricing” lists no additional platform account/payout fees in that model.
“You handle pricing” lists **$2 per monthly active account** and **0.25% + $0.25 per payout**.
Processing, Billing, instant/cross-border payouts, tax reporting and other options can
add costs. These are reference line items, not a complete Genesis quote or guarantee.

Existing Square reference: standard US Online API card processing **2.9% + $0.30**;
seller contracts, channels and additional services can differ.

Before implementation/activation: approve the provider architecture, identify the
contracting merchant(s), confirm provider eligibility/liability/refund arrangements,
approve pricing and lawful commissions, connect through the supported authorization
flow, then validate authorized test-mode scenarios. Live money movement remains gated.

## Sources reviewed

- Stripe charge types: https://docs.stripe.com/connect/charges
- Stripe Connect disputes: https://docs.stripe.com/connect/disputes
- Stripe Connect pricing: https://stripe.com/connect/pricing
- Square application fees: https://developer.squareup.com/docs/payments-api/take-payments-and-collect-fees
- Square Payouts: https://developer.squareup.com/reference/square/payouts-api
- Square US fees: https://squareup.com/us/en/payments/our-fees
