# Replit deployment
1. Import this repository/ZIP into Replit.
2. Provision a PostgreSQL database and set GENESIS_DATABASE_URL.
3. Create a random GENESIS_JWT_SECRET of at least 64 characters even though browser sessions are now opaque; it remains reserved for server-side signing integrations.
4. Set GENESIS_ENV=production, GENESIS_COOKIE_SECURE=true, GENESIS_ALLOWED_HOSTS to your deployment/custom domain, and GENESIS_ALLOWED_ORIGINS to the exact HTTPS origin.
5. Store all secrets in Replit Secrets/environment variables; never commit .env.
6. Deploy behind HTTPS. Verify /healthz, login, logout, CSRF rejection, tenant isolation, Lockdown Mode, and security headers before accepting user data.
7. Add a passkey/WebAuthn identity provider before privileged production use.
