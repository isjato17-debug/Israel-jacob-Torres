---
name: Production-readiness scope
description: User boundaries for Genesis production preparation and QA cleanup.
---

For Genesis production-readiness preparation, preserve the approved interface and existing functionality; this is infrastructure work, not another redesign.

**Why:** The user explicitly requested production infrastructure rather than further visual redesign.

**How to apply:** Keep changes limited to readiness controls, verification and evidence; do not replace the product or hosting platform to bypass an unavailable account or credential.

Delete only data created solely by the latest authenticated QA run, and prove pre-existing data unchanged. New browser QA should use a separate disposable database and be destroyed afterward.

**Why:** Earlier browser QA left a disposable workspace in the development database, and the user required scoped cleanup without changing unrelated data.

**How to apply:** Verify exact ownership before cleanup and compare all non-target rows before committing. Keep subsequent browser verification away from the active development database.

External EXECUTE providers must remain NEEDS_CONNECTION until actual credentials are supplied and verified. Do not fabricate production evidence or publish automatically; report deployment safety and stop at unavailable infrastructure boundaries.

**Why:** These are explicit user boundaries for this phase.

**How to apply:** Distinguish local tests from live certification, and promote canonical gates only from evidence that meets the gate.
