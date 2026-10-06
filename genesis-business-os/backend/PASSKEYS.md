# Passkey production boundary
Genesis Business OS v4 removes bearer tokens from browser storage and uses server-side revocable sessions.
For production, connect a WebAuthn/FIDO2 identity provider or implement WebAuthn registration/authentication with a mature audited library. Require passkeys for owners/admins and step-up authentication for Tier 3/4 approvals.
Do not implement home-grown WebAuthn cryptography.
