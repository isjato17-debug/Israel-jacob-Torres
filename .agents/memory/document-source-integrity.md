---
name: Generated document source integrity
description: Why document rendering and revision-specific approval must remain reproducible across future template changes.
---

Keep generated document revisions immutable, including their rendering version.
Preserve old renderers when adding a new template version; do not overwrite old
sources or relabel an earlier approval as approval of new content.

**Why:** The current no-paid-service workflow stores private structured document
source rather than file bytes or a public/cloud copy. Downloads are rendered on
demand, and customer approval binds to the exact generated file hash. Changing an
old renderer would otherwise invalidate existing downloads and approved evidence.

**How to apply:** Version output-changing template edits, retain compatible old
rendering paths, and verify old byte hashes. Corrections create a new revision and
require new approval; historical approvals remain evidence, not current readiness.

Keep test-signature renderers reproducible too. Coordinate any audit-key rotation
with preserved historical verification access or a reviewed evidence migration;
do not silently relabel unverifiable history as verified.

**Why:** Private test copies bind both the original document and a server audit
MAC. A key change can make an otherwise unchanged historical copy fail verification.

**How to apply:** Treat key lifecycle as an operational prerequisite before
production signing; this development test mechanism is not independent legal proof.
