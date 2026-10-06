# Genesis Business OS — Real Execution Matrix

Genesis never treats a button click as proof of completion.

| Business action | Genesis mode | Execution point | Verification |
|---|---|---|---|
| Send outreach/customer email | EXECUTE | SendGrid Mail Send after account credential is connected | provider acceptance/message reference |
| Create customer/CRM record | EXECUTE | Square Customers API after seller authorization | Square customer ID |
| Create payment link | EXECUTE | Square Checkout API after seller authorization/location configuration | Square payment-link ID + URL |
| Prepare business plan | PREPARE | Genesis deterministic document preparation | stored artifact |
| Prepare offer/outreach/pricing/launch checklist | PREPARE | Genesis preparation engine | stored artifact |
| Apply for EIN | GUIDE | Official IRS EIN application | user-supplied completion evidence; Genesis does not claim filing |
| Registration/licenses/permits review | GUIDE | Official SBA/issuing-agency path | user/agency evidence |

## Execution lifecycle
PROPOSED → AWAITING_APPROVAL (when required) → APPROVED → EXECUTED/PREPARED/GUIDED → evidence → VERIFIED.

Provider credentials are server-side environment secrets. Missing credentials produce `NEEDS_CONNECTION`; they never produce simulated success. Tier-4 autonomous EXECUTE remains disabled. External consequential actions require explicit approval. Repeated `perform` calls return the existing terminal result rather than creating another action.

## Still requires deployment/account authorization
The code contains the connection points, but actual external execution cannot occur until the business owner supplies/authorizes the relevant provider account in the deployed environment. Government identity/signature steps remain owner-controlled official handoffs.
