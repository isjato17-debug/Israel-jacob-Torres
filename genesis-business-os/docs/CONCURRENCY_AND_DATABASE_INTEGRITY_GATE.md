# Concurrency & Database Integrity Gate
Before public production:
- add reviewed PostgreSQL foreign keys for tenant/user/business/evidence/decision/session/community relationships where lifecycle semantics allow;
- define ON DELETE behavior explicitly;
- add optimistic concurrency/version checks to mutable Business Twin and route state;
- reject stale writes rather than silently overwriting a newer version;
- make provider action/evidence transitions transactional;
- use unique/idempotency constraints for provider writes;
- test simultaneous approvals, actual-result updates, community mutations and account deletion;
- run migrations against a production-like copy and test rollback/restore.
Application tenant checks remain mandatory even after DB constraints are added.
