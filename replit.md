# B.I.G. — Business Inside Genesis

See `docs/BIG_PHASE2_IMPLEMENTATION.md` under `genesis-business-os/` for the current
brand implementation, no-cost development boundaries and remaining production requirements.
See `docs/BIG_PARTNER_NETWORK_FOUNDATION.md` in the same directory for private partner
intake/review boundaries. Review preserves tenant scope and the explicit operator allowlist;
manual evidence is not a connected API or government endorsement. No partner activation,
external promotion, filing or paid service is authorized.

## Permanent core intelligence directive

The full additive product directive is preserved in
[`attached_assets/Pasted--B-I-G-GENESIS-OS-2-0-PERMANENT-CORE-INTELLIG-179209375_1792093759891.txt`](attached_assets/Pasted--B-I-G-GENESIS-OS-2-0-PERMANENT-CORE-INTELLIG-179209375_1792093759891.txt).

- B.I.G. is an intelligent, full-service business consultant and operating system,
  not merely a document-preparation, filing or service-provider application.
- One persistent, personalized assistant should think and plan with customers,
  explain decisions, remember authorized business context and adapt recommendations.
  Connect it to actual Business Projects, financial records, tasks and documents.
- Preserve the existing design, architecture and every existing feature, including
  Founder DNA, Digital Twin, Executive Board, Battle Mode, Mission Control and financial
  intelligence. Reuse these systems; do not create duplicate dashboards or unnecessarily
  repeat questions. Keep advanced tools available without complicating the main interface.
- Combine consulting with supported execution: prepare work, obtain review and required
  signatures, coordinate authorized submissions, track verified outcomes, and help manage
  operations, finances, compliance, funding and growth throughout the business's lifetime.
  Never invent financial results or claim an action occurred without evidence.
- Continuous intelligence must use source-backed, versioned information. With appropriate
  customer permissions, identify obligations, missing documents, shortfalls, funding matches,
  unfinished tasks and practical improvements. Do not silently modify production code or
  activate unverified legal interpretations.
- Do not substitute scripted responses for genuine AI capabilities. Clearly distinguish
  connected AI from capabilities not yet activated; existing deterministic features must
  remain honestly labeled. Paid AI activation requires explicit owner approval.
- Require explicit approval for external filings, signatures, payments and sensitive
  information sharing. Deployment and external filings remain blocked without authorization.
- Implement enhancements in tested, dependency-ordered milestones. Do not interrupt
  currently authorized AutoForm development. This permanent product direction does not,
  by itself, expand the separately authorized implementation milestone.

## Owner execution and service-connection direction

The owner explicitly requires functioning application code, not documentation in
place of implementation: build and verify one connected $3,000 New York cleaning
business consultation → existing selected plan/project → authorized information reuse
→ genuine document → corrections/download → explicit review approval → signature
preparation → persisted next action. Preserve the complete existing app and design;
use additive migrations, isolated QA and tested local commits on
`genesis-os-2-development`. Protected main, Git credentials and publishing remain untouched.

**Why:** The owner corrected the earlier documentation-only response and supplied an
explicit direct execution order.

The owner requests external services on standby for coordinated connection when ready:
“Yes have them all on stand by so when it's time To connect services we can do it all
one shot” and “Yes add the external we just wait for the payed ones”.
Prepare extensible connection requirements and no-cost public reads where supported,
but wait on paid services. Connection is not permission for filings, signatures,
payments or sensitive-data sharing. Do not imply every provider can activate in one
operation or that an unimplemented adapter is ready.

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
- Keep the Genesis UI scripts external and compatible with a strict `script-src 'self'` Content Security Policy in every environment.
- Treat provider-dependent actions as unavailable until a real, approved provider connection is configured and verified.

## Product

The app supports founder onboarding, business planning, route evolution, evidence capture, execution preparation, outcomes, and a business-focused community. The imported package is a development/reference implementation, not a production-readiness claim.

## User preferences

No additional user preferences recorded.

## Gotchas

- Run each imported test suite from its own directory; the execution-layer test imports are relative to `execution_layer/app`.
- The frontend is served from `genesis-business-os/frontend`; use B.I.G. customer branding
  while preserving existing features and the `/`, `/next/`, `/next/owner/` routes.
- External email, payment, AI, and other provider actions remain unavailable until their integrations and production configuration are established.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
