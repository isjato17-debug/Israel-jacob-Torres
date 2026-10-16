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

Disposable PostgreSQL databases must use UTF-8 rather than SQL_ASCII.

**Why:** Locale-free PostgreSQL initialization here can default to SQL_ASCII;
psycopg then returns bytes where SQLAlchemy expects text, causing connection
initialization errors unrelated to the app's migrations.

**How to apply:** Check the disposable database encoding before interpreting
PostgreSQL connection failures as application regressions.

Workspace restarts can remove `/tmp` data and terminate background processes and
in-flight helper assignments. Keep recovery copies in an excluded workspace
directory, not solely under `/tmp`.

**Why:** A workspace restart removed a disposable PostgreSQL data directory and
interrupted browser acceptance even though source files and workspace SQLite
fixtures survived.

**How to apply:** Resume the same saved QA journey where possible; distinguish
an interrupted verification session from an application failure.

Temporary development environment overrides can leave empty configuration
tables after deletion. Verify exact configuration restoration, not only that
the two temporary values disappeared.

**Why:** Removing disposable-QA overrides left empty user-environment tables;
direct configuration edits are rejected by this workspace.

**How to apply:** Preserve a baseline before temporary QA overrides, remove
their values with the environment tools, then restore any structural residue
through the schema-validating configuration replacement callback. Never change
the normal database target or owner allowlist permanently for a browser test.
