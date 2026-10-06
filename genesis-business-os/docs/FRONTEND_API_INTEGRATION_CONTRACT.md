# Frontend/API Integration Contract — Required Before Production

The included Genesis visual frontend is the design/reference shell. It must not be represented as fully live until wired to backend APIs.

Required wiring:
1. Authentication: register/login/me/logout; keep session in HttpOnly cookie; keep CSRF token in memory and refresh it through an authenticated bootstrap strategy—never local/session storage.
2. Founder Reality: save/read profile with validation and explicit error state.
3. Route: call portfolio, next-turn, counterfactual and reroute endpoints; show loading/error/retry; never advance proof from a local checkbox alone.
4. Do It: show EXECUTE/PREPARE/GUIDE, approval state, provider availability, evidence and VERIFIED/FAILED status.
5. Community: feed/create/reply/report/block/delete; surface moderation and network errors.
6. Ask Genesis: authenticated consultant endpoint; label assumptions/evidence and provider limitations.
7. My Business: server-backed business state, twin version, evidence and actual results.
8. Lockdown: disable external-write CTAs and explain read/recommend-only mode.
9. Accessibility: semantic labels, visible keyboard focus, dialog focus management, status announcements, reduced-motion support, contrast validation and 320px viewport test.
10. Failure states: unauthenticated, 403, 404, 409 stale write, 423 lockdown, 429 rate limit, 5xx, timeout/offline, provider unavailable and ambiguous provider result.

A successful visual click is never proof that a backend/provider action succeeded.
