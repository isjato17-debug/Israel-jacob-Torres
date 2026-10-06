# Genesis Business OS Security

## Security invariants
1. Every business object is tenant-scoped and backend authorization is mandatory.
2. AI/model output is untrusted. It cannot expand permissions.
3. External actions pass an independent authorization gateway.
4. Tier-4 actions are non-autonomous in this MVP.
5. Production secrets never belong in source code, prompts, logs, or client storage.
6. Lockdown mode disables write/action operations for a tenant.

## Production requirements before real customer data
- Replace local JWT storage with a hardened identity provider using passkeys/WebAuthn or phishing-resistant MFA and secure HttpOnly cookies/session tokens.
- PostgreSQL with row-level security; per-tenant object authorization tests.
- Managed KMS/secrets vault; TLS everywhere; private DB networking.
- WAF/DDoS protection, centralized SIEM/security logs, anomaly alerts.
- CSP without unsafe-inline by moving styles to static CSS.
- CSRF protections if cookie auth is used.
- SAST, dependency/SBOM, container and IaC scanning; signed builds.
- Independent penetration test and AI red-team before production.
- Encrypted immutable backups and restore exercises.
- Incident response, vulnerability disclosure, key rotation, access reviews.

## AI threat model
Defend against prompt injection, malicious uploads, tool-output injection, excessive agency, sensitive-data disclosure, cross-tenant retrieval, poisoned sources, insecure output handling, unbounded resource use, and compromised connectors. External content is data, never policy.
