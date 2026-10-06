# Genesis Real Execution Layer
This package adds the execution truth layer to Genesis.

It implements:
- EXECUTE / PREPARE / GUIDE action modes
- resource trust records
- risk tiers and approval requirements
- evidence receipts
- verification gates
- hard refusal to fake a live integration
- Tier-4 autonomous execution prohibition

This is the provider-independent execution core. Real external execution becomes active only when the corresponding provider adapter/credentials/permissions are connected in production.
