---
name: Gate matrix reconciliation
description: Keep overlapping Genesis gate-matrix snapshots internally consistent when reporting status.
---

Calculate overall gate totals from the current full matrix. Do not combine those totals with a separately generated subset matrix until the overlapping rows have been reconciled.

**Why:** overlapping snapshots can disagree, producing impossible per-range totals if their statuses are mixed.

**How to apply:** recompute status counts from the full matrix before reporting the 1,000-gate result, and explicitly disclose any conflicting subset rather than silently averaging or replacing its values.
