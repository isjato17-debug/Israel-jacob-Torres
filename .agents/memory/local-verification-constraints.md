---
name: Local verification constraints
description: Caveats for Genesis browser-auth tests and disposable PostgreSQL in this Replit workspace.
---

The email-validation dependency rejects `.test` addresses as a reserved special-use domain. Use unique addresses under `example.com` for browser tests that exercise registration.

**Why:** A syntactically plausible test address can fail server-side validation before the browser flow runs.

**How to apply:** Use `example.com` addresses in app-level auth tests; do not interpret a `.test` validation failure as an authentication regression.

Disposable PostgreSQL initialized in this workspace uses the `runner` role rather than a `postgres` role. Keep the server alive in a background shell during tests and select `runner` explicitly for client commands.

**Why:** The default database role and process lifetime do not match common local PostgreSQL assumptions.

**How to apply:** For temporary migration tests, use the initialized workspace role and keep the server process persistent until migration and startup checks finish.
