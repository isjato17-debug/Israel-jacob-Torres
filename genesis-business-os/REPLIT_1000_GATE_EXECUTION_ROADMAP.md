# Replit Execution Roadmap — Converting RELEASE GATES to PASS

## Phase 1 — Make the visual product live
Wire the consumer frontend to authentication, Founder Reality, Business state, Route Portfolio, Next Turn, Reroute, Counterfactual, Community, Ask Genesis and execution/evidence APIs. Implement loading, empty, 401/403/404/409/423/429/5xx, timeout/offline and provider-unavailable states. Add accessibility semantics and keyboard/focus behavior.

## Phase 2 — Production data plane
Move production to PostgreSQL. Create reviewed Alembic migrations, foreign keys, unique/idempotency constraints, optimistic version checks and transactional action/evidence transitions. Test rollback and restore.

## Phase 3 — Identity and authorization
Implement passkeys/MFA/recovery, session rotation, revoke-all/device management and step-up authentication. Run IDOR, privilege-escalation, CSRF, CORS, host-header and cross-tenant tests.

## Phase 4 — Real provider execution
For each provider adapter implement connection/permission validation, scoped capabilities, explicit approval, idempotency, timeouts, bounded retry, signed webhooks, replay defense, receipts, reconciliation and circuit breakers. Never mark ambiguous external results VERIFIED.

## Phase 5 — AI adversarial security
Run prompt-injection, indirect-injection, retrieval-poisoning, malicious-upload, fake-approval, tool-call-injection, secret-extraction, SSRF, cross-tenant retrieval and exfiltration suites. Keep model/retrieved text incapable of granting permissions.

## Phase 6 — Financial correctness
Move currency to Decimal/fixed-point where accounting-grade precision matters. Version formulas/assumptions. Test zero/negative/extreme cases, refunds, chargebacks, debt, inventory, seasonality and tax/fee applicability.

## Phase 7 — Community production safety
Add moderation queue/admin tooling, spam/report throttling, scam/impersonation/doxxing handling, appeals and abuse metrics. Test block/report/delete under concurrency.

## Phase 8 — Production validation
Run browser/device/accessibility testing, load/stress/soak tests, dependency/security scans, penetration testing, observability alerts, backup/restore drills, account export/deletion, connector revocation and Lockdown/disaster exercises.

Do not convert a RELEASE GATE to PASS based only on documentation or a UI mock. Require executable evidence.
