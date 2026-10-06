# Genesis Business OS - Replit deployment
Run command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Required production Secrets
GENESIS_ENV=production
GENESIS_DATABASE_URL=<managed PostgreSQL connection string>
GENESIS_JWT_SECRET=<64+ random characters>
GENESIS_ALLOWED_ORIGINS=https://<your-domain>
GENESIS_ALLOWED_HOSTS=<your-domain>
GENESIS_COOKIE_SECURE=true

Optional AI provider secrets (server side only): GENESIS_AI_PROVIDER, GENESIS_AI_BASE_URL, GENESIS_AI_MODEL, GENESIS_AI_API_KEY.
Never put secrets in source files or browser JavaScript. Use Replit Secrets/environment variables.
