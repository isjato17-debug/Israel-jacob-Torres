# Genesis Business OS

A founder-focused business operating system that turns a business goal and current resources into guided next steps, evidence checkpoints, and rerouted plans.

## Run & Operate

- Start the `Genesis Business OS` workflow to run the imported FastAPI app and its supplied consumer interface.
- The development database is SQLite in `genesis-business-os/backend`; production must use PostgreSQL.
- Run backend tests from `genesis-business-os/backend` with `pytest -q`.
- Run execution-layer tests from `genesis-business-os/execution_layer` with `PYTHONPATH=app pytest -q`.
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Product app: Python 3.13, FastAPI, SQLAlchemy, SQLite for local development
- Workspace API scaffold: Express 5, PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `genesis-business-os/backend/` — imported FastAPI app, models, routes, static UI, and backend tests.
- `genesis-business-os/execution_layer/` — imported execution module and tests.
- `genesis-business-os/docs/` — product, security, UX, and release-gate references from the uploaded package.
- `artifacts/api-server/` and `artifacts/mockup-sandbox/` — existing workspace scaffold artifacts.

## Architecture decisions

- Keep the uploaded FastAPI app as the product source instead of rewriting its backend into the workspace's Express scaffold.
- Allow the imported inline UI scripts only in development; the production Content Security Policy remains strict.
- Treat provider-dependent actions as unavailable until a real, approved provider connection is configured and verified.

## Product

The app supports founder onboarding, business planning, route evolution, evidence capture, execution preparation, outcomes, and a business-focused community. The imported package is a development/reference implementation, not a production-readiness claim.

## User preferences

No additional user preferences recorded.

## Gotchas

- Run each imported test suite from its own directory; the execution-layer test imports are relative to `execution_layer/app`.
- The bundled UI uses inline scripts and event handlers. Production CSP compatibility must be resolved before production use.
- External email, payment, AI, and other provider actions remain unavailable until their integrations and production configuration are established.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
