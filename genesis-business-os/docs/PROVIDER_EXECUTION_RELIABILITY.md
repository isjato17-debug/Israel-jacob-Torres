# Provider Execution Reliability
Every external write uses an idempotency key bound to tenant, user, action, provider and payload hash. Replays must return the prior result or fail safely, never duplicate spend/messages/filings.

Provider adapters must implement:
- connection/permission check before execution
- explicit approval where risk policy requires it
- timeout and bounded retry policy
- signed webhook verification when webhooks are used
- replay protection
- provider receipt/external reference capture
- failure state that does not mark the action complete
- reconciliation job for ambiguous timeout states
- circuit breaker/disable switch
- audit event for request, authorization, provider result and verification
