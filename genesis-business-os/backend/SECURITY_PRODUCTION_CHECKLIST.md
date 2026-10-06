# Production Security Gate

Do not accept sensitive customer data until every blocking item is complete.

## Blocking before public launch
- Managed PostgreSQL; backups and restore test.
- 64+ character random JWT/signing secret in secret manager.
- Production HTTPS only; HSTS enabled.
- Phishing-resistant MFA/passkeys through a hardened identity provider for owner/admin accounts.
- Server-side session or hardened HttpOnly/Secure/SameSite cookies; do not persist bearer tokens in localStorage.
- Distributed rate limiting at edge/API gateway and credential-stuffing controls.
- WAF/DDoS protection.
- Object-level tenant authorization tests on every resource endpoint.
- KMS/secrets manager; no credentials in repo, logs, prompts, URLs, or client code.
- Separate development/staging/production credentials and data.
- Centralized security logs with alerts; audit store protected from application-user modification.
- Dependency, SAST, container and secret scanning in CI.
- SBOM and signed production images/releases.
- Encrypted backups, tested recovery and incident-response runbook.
- Independent web/API penetration test and AI prompt-injection/tool-abuse red team.
- Privacy/retention/deletion policy and applicable legal review.

## AI action safety
- Model output is untrusted data.
- Tool allowlist + strict schemas + tenant-scoped service identity.
- No model can create/expand its own permission.
- External write/spend/export actions pass independent policy evaluation.
- High-consequence actions require reauthentication and human approval.
- Lockdown revokes capabilities and forces recommendation-only mode.
