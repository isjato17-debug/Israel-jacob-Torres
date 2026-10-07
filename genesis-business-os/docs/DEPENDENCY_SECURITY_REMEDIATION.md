# Genesis dependency-security remediation

Verification date: **2026-10-06, America/New_York** (tool timestamps also include 2026-10-07 UTC).

**Dependency security blocker cleared: YES. Safe to begin live infrastructure setup: YES. Safe to deploy: NO.**

This is dependency remediation and local verification, not live production certification. No deployment, provider connection, gate promotion, redesign, feature removal or production-data operation was performed.

## Before → after

| Severity | Raw scan entries before | Distinct advisories before | After |
| --- | ---: | ---: | ---: |
| Critical | 1 | 1 | 0 |
| High | 4 | 4 | 0 |
| Moderate | 9 | 4 | 0 |
| Low / informational | 0 | 0 | 0 |
| **Total** | **14** | **9** | **0** |

The six pytest entries are repetitions and PYSEC/GHSA aliases for one CVE, not six separate vulnerabilities. The three brace-expansion advisories are genuinely distinct. The baseline covers **7 vulnerable packages**.

Post-remediation dependency audit: **0 Critical / 0 High / 0 Moderate / 0 Low / 0 Informational**. Static security scan completed with **0 findings**; privacy/data-flow scan returned **0 findings**.

## Every distinct advisory and actual exposure

| Package / installed baseline | Advisory / CVE | Severity | Actual vulnerable-path exposure | Resolution |
| --- | --- | --- | --- | --- |
| proxy-addr 2.0.7 | GHSA-jqcg-44mw-7w3h / CVE-2026-90711 | Critical | Express 5.2.1 in the retained Node API scaffold. Exploitable proxy trust bypass requires a short IPv4-mapped IPv6/zero-leading IPv6 trust subnet; that configuration is not present. The managed Genesis API runs Python Uvicorn, not this scaffold. Dormant runtime dependency still needed patching. | 2.0.8; malformed mapped-subnet trust regression passed. |
| brace-expansion 5.0.9 | GHSA-6j4f-fj2g-mc7p / CVE-2026-102276 | High | Orval → TypeDoc → minimatch; malicious glob comma parsing can exhaust the stack. Used by development/code-generation tooling, not the Python request path. No app endpoint accepts glob input into this chain. | 5.0.12; parsing recursion regression passed. |
| brace-expansion 5.0.9 | GHSA-qhr7-859c-m2p7 / CVE-2026-102278 | High | Same tooling chain; deep nesting can exhaust the stack. | 5.0.12; nested-expansion regression passed. |
| brace-expansion 5.0.9 | GHSA-q2hr-2g5m-vwhr / CVE-2026-102277 | Moderate | Same tooling chain; repeated closing-brace rewrites cause quadratic work. | 5.0.12; bounded rewrite regression passed. |
| braces 3.0.3 | GHSA-vfj7-8cjw-p6xm / CVE-2026-93687 | High | Mockup sandbox fast-glob 3.3.3 → micromatch 4.0.8. The plugin used a constant trusted discovery pattern, not a visitor-supplied pattern; malicious patterns could otherwise overflow AST recursion. | No patched release was listed. Removed the chain by replacing discovery with native filesystem traversal, not by ignoring the finding. |
| source-map-js 1.2.1 | GHSA-68fv-2mgg-jv7q / CVE-2026-93749 | High | Tailwind/Vite/PostCSS build chain; excessively large indexed-source-map section offsets can block synchronous work. No app endpoint parses uploaded source maps using it. | 1.2.2; excessive offset rejection regression passed. |
| fast-uri 3.1.7 | GHSA-hrr3-gc8f-f4qj / CVE-2026-86472 | Moderate | Orval → Scalar OpenAPI parser → AJV. Scheme-relative percent-encoded host normalization can evade case-sensitive host checks. Genesis host/origin enforcement does not use this parser. | 3.1.8, retained major version; normalization/equality regression passed. |
| postcss-selector-parser 6.0.10 | GHSA-rj75-hqrm-r3gf / CVE-2026-104844 | Moderate | @tailwindcss/typography 0.5.20 build dependency. Malicious flat selectors can cause quadratic parsing; ordinary trusted build sources are not the attack scenario. No app endpoint processes attacker-supplied CSS through this package. | 7.1.6; targeted parent override with selector and typography compatibility verification. |
| pytest 8.4.2 | PYSEC-2026-1845 / GHSA-6w46-j5rx-g56g / CVE-2025-71176 | Moderate | Root/backend/execution test tooling on UNIX. Predictable temporary directories permit a local attacker to deny service or potentially gain privileges. Not an HTTP request dependency. | 9.1.1, newer than the 9.0.3 security fix; all declared constraints updated to >=9.0.3,<10 and complete test suites passed. |

Trusted-source/build-only exposure does not excuse a vulnerable dependency. All nine advisory groups were addressed; none was suppressed or accepted as an outstanding exception.

## Every changed dependency

### Upgraded

| Dependency | Before | After |
| --- | --- | --- |
| proxy-addr | 2.0.7 | 2.0.8 |
| brace-expansion | 5.0.9 | 5.0.12 |
| source-map-js | 1.2.1 | 1.2.2 |
| fast-uri | 3.1.7 | 3.1.8 |
| postcss-selector-parser | 6.0.10 | 7.1.6 |
| pytest | 8.4.2 | 9.1.1 |

### Removed from the dependency graph

All entries below changed from the stated version to **removed**. These are the complete 18 removed nodes, including the no-longer-needed helpers of the replaced globbing chain.

| Dependency | Removed version |
| --- | --- |
| fast-glob | 3.3.3 |
| micromatch | 4.0.8 |
| braces | 3.0.3 |
| @nodelib/fs.scandir | 2.1.5 |
| @nodelib/fs.stat | 2.0.5 |
| @nodelib/fs.walk | 1.2.8 |
| fastq | 1.20.3 |
| fill-range | 7.1.1 |
| glob-parent | 5.1.2 |
| is-extglob | 2.1.1 |
| is-glob | 4.0.3 |
| is-number | 7.0.0 |
| merge2 | 1.4.1 |
| picomatch | 2.3.2 |
| queue-microtask | 1.2.3 |
| reusify | 1.1.0 |
| run-parallel | 1.2.0 |
| to-regex-range | 5.0.1 |

Native discovery preserves nested TSX files, linked preview folders, and underscore/dot exclusions. It additionally avoids traversing symlink cycles. The mockup production output retained the same CSS/JS asset filenames after replacement.

### Compatibility and installation decisions

- Four transitive patch pins retain their existing major versions and satisfy current parent ranges: proxy-addr, brace-expansion, source-map-js and fast-uri. Existing parents were retained rather than upgrading unrelated tooling or application APIs.
- Express's latest inspected version was still 5.2.1. Typography's latest inspected version was still 0.5.20 and pinned vulnerable parser 6.0.10. A parent-specific parser override was necessary rather than an unrelated application-library swap.
- Seven selector fixtures produced identical text/AST node types before and after the parser upgrade. Compiled `prose`, `prose-lg` and `prose-invert` CSS was **byte-identical: 22,942 bytes**.
- pytest's major upgrade required no application/test changes: **39 backend + 3 execution tests passed**.
- Manifests and both `pnpm-lock.yaml` and `uv.lock` were updated. Python lock comparison showed only pytest's version changed. Node lock comparison showed exactly five replacements and the eighteen removals above.
- Runtime-resolved versions were checked through the actual Express, TypeDoc/minimatch, AJV, Vite/PostCSS and typography dependency paths. A clean lockfile-only audit was not treated as proof until the installed modules were synchronized and checked.
- `minimumReleaseAge: 1440`, the existing package firewall and build allowlist were preserved. No supply-chain protection was disabled.

## Exact verification results

| Verification | Result |
| --- | --- |
| Dependency audit | 0 findings in all severities |
| Static security scan | Complete; 0 findings |
| Privacy/data-flow scan | 0 findings |
| Dependency security regressions | **9 passed, 0 failed, 0 skipped** |
| Backend suite | **39 passed**, 2 pre-existing dependency deprecation warnings |
| Execution-layer suite | **3 passed** |
| Full workspace TypeScript check | Passed, including shared libraries, API scaffold, Genesis app, scripts and mockup sandbox |
| Genesis production frontend build | Passed: `PORT=5173 BASE_PATH=/ pnpm --filter @workspace/genesis-app run build` |
| Mockup sandbox production build | Passed after native discovery replacement |
| Retained Node API scaffold build | Passed |
| Disposable PostgreSQL 17.5 migration | Upgrade → downgrade to base → upgrade passed; 19 public tables after upgrade; only Alembic revision table after rollback; current revision **g0001 (head)** |
| Alembic schema drift check | **No new upgrade operations detected** |
| Local production-mode startup | Passed against the migrated disposable PostgreSQL database with synthetic test-only settings |
| Local production-mode security headers and boundaries | CSP script self/anti-framing, HSTS, no-sniff, unauthenticated rejection and untrusted Host rejection passed |
| Production fail-closed configuration checks | 5 passed: missing secret, SQLite URL, insecure cookies, HTTP origins, wildcard hosts |
| Provider state | email_send, crm_customer_create and payment_link_create all **NEEDS_CONNECTION** |
| Managed workflows | All three restarted and served requests without startup errors |
| Active preview screenshot | Approved sign-in UI rendered; signed-out `/api/me` 401 expected |
| Active development data | Full table counts and row digests matched baseline; **11 existing tenants retained**, no record changes |
| Approved frontend | All source/file fingerprints matched baseline: **byte-identical** |
| Canonical release matrix | **400 PASS / 0 FAIL / 600 RELEASE GATE**; 1,000 distinct gates; no status promoted |

Regression command: `pnpm --filter @workspace/scripts run security:dependencies`.

The two suite warnings concern Starlette's future HTTP client choice and Passlib's deprecated Argon2 version lookup. They were not vulnerability findings or test failures.

## Fresh authenticated browser pass

One Chromium pass ran only against a temporary independent SQLite database. It did not use or modify the active development database.

1. **Registration/workspace/journey: PASS.** Three routes calculated; destination/profile/progress persisted across reload.
2. **Ask Genesis: PASS for integration.** Actual `POST /api/consultant/generate` returned HTTP 200 and displayed the response.
3. **Business DNA: PASS.** Saved capital 12,000, hours/week 25, experience 8 years and risk 6 persisted; derived readiness 50 and corresponding bands appeared.
4. **Evolution: PASS.** Saved actuals appeared on Home; comparison recommended “Strengthen repeat customers,” fit 66.2/100 and $525 cash envelope.
5. **Community: PASS.** Created Ask post, category filtering hid/restored it, and a new reply appeared.
6. **Prepared actions/provider gating: PASS.** `business_plan_prepare` was VERIFIED; provider controls remained disabled with NEEDS_CONNECTION. No external request was observed.
7. **Logout/re-login persistence: PASS.** Same workspace and saved destination, actuals, progress and community data returned.

At **402×844**, populated Home, Ask Genesis, My Business, Community and Do It all had **document/body clientWidth = scrollWidth = 387px**, with viewport innerWidth 402px; the 15px difference is the vertical scrollbar. **No horizontal overflow**. Controls were visible/reachable, including the scrolled Community composer and replies.

No JavaScript pageerror or CSP violation was observed. Signed-out 401s and the isolated FastAPI server's favicon 404 were expected, not authenticated-flow failures.

Non-blocking, pre-existing/out-of-scope observations were retained without redesign: the Ask response was generic rather than directly addressing the validation question; a hidden auth-status element retained “Working…” after successful sign-in; Home's narrow journey-hero labels were crowded. Endpoint/functional verification does not certify AI answer quality or full accessibility.

The independent browser database and disposable PostgreSQL server/database were stopped and removed after verification. No QA workspace was left in the active development database.

## Remaining vulnerabilities and live boundary

**Remaining reported dependency vulnerabilities: none. Unfixed advisory groups: none.**

This is the result of the current scanner/advisory database and reviewed dependency graph, not a guarantee that future advisories cannot appear.

Live infrastructure setup may now begin, but it was not performed. Production PostgreSQL credentials/TLS/privileges, real HTTPS hosting/domain/proxy behavior, production session/cookie behavior, backup/restore, load/concurrency, shared rate limiting and remaining security/privacy/AI/provider release evidence are still unverified. External EXECUTE providers remain NEEDS_CONNECTION until supplied credentials are securely configured and verified.

No production environment variables, external integrations or credentials were changed. No publishing was performed. All **600 RELEASE GATES** remain release gates.

**DEPENDENCY SECURITY BLOCKER CLEARED: YES**

**SAFE TO BEGIN LIVE INFRASTRUCTURE SETUP: YES**
