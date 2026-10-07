---
name: Dependency verification
description: Distinguish lockfile scan results from the versions actually loaded in development.
---

After dependency remediation, verify the runtime-resolved versions along the actual parent dependency paths, not only scanner results or lockfile entries.

**Why:** Node package installation reported success and the dependency audit returned zero findings while the development runtime still resolved the old vulnerable transitive versions. Repeating installation, including a forced installation, did not synchronize those modules; reconciliation from the frozen reviewed lockfile did.

**How to apply:** Check both the manifest/lock and actual module resolution before declaring a dependency blocker cleared. Preserve release-age and firewall protections during reconciliation. If the graph differs, synchronize from the reviewed lockfile before compatibility tests or runtime builds.
