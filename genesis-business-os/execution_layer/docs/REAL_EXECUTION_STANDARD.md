# GENESIS REAL EXECUTION STANDARD

## Non-negotiable promise
A Genesis button must never imply that an external action happened when it did not.

Every action is exactly one of:
- EXECUTE — a supported connected provider/action actually performs it.
- PREPARE — Genesis creates a finished, usable artifact or structured submission package for review.
- GUIDE — Genesis uses a verified destination/source and guides the user through an action that Genesis cannot lawfully/technically perform.

## Action lifecycle
RECOMMEND -> EXPLAIN -> APPROVE (when required) -> EXECUTE/PREPARE/GUIDE -> CAPTURE EVIDENCE -> VERIFY -> UPDATE BUSINESS STATE -> REROUTE/NEXT TURN.

## Evidence
Examples: provider receipt/ID, authoritative confirmation, signed webhook, accepted submission status, user-confirmed real-world result with provenance, generated artifact hash, analytics result.
AI-generated prose alone is not evidence that an external action occurred.

## Resource trust record
Every external resource stores provider name, authority level, jurisdiction, capabilities, connection requirement, verified destination where appropriate, last checked date, and notes.

## Risk
Tier 0 read/analyze.
Tier 1 draft/prepare.
Tier 2 reversible internal change.
Tier 3 external communication/spend/configuration requires explicit approval.
Tier 4 high-consequence financial/contractual/destructive/sensitive action: autonomous execution disabled.

## Route integration
A Proof Checkpoint consumes verified evidence. Failed or weak results feed the Reality Loop and can trigger dependency-selective rerouting. Completion cannot be manufactured by checking a UI box.
