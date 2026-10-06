# Session & Authentication Hardening Gate
Current sessions are random, server-recorded, revocable, idle/absolute-expiring cookies. Before public production additionally prove:
- session ID rotation after authentication and privilege change;
- revoke all sessions after password reset/security event;
- MFA/passkey enrollment and recovery path;
- no account enumeration in recovery;
- recovery token single use, short expiry and hashed storage;
- concurrent-session/device visibility;
- step-up authentication for sensitive Tier 3/4 actions;
- proxy-aware client IP handling only from trusted proxy headers;
- clock-skew/expiry tests;
- cookie behavior in the actual production domain and browser matrix.
