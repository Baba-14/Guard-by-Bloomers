# Guard

Guard is a Ghana-first fraud-prevention and fraud-intelligence MVP.

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

`npm run dev` starts both the Next.js website and the FastAPI analysis service.
The website runs on port 3000 and the API runs on port 8000.

Demo login is enabled by default in development. Use `user@guard.test` or
`admin@guard.test` with password `guard123`. Production builds keep these demo
accounts disabled unless `NEXT_PUBLIC_ENABLE_DEMO_AUTH=true` is explicitly set.

Development uses `.next`; production builds use `.next-build`, so running a build will not invalidate an active development server. Do not run two `next dev` processes against the same port.

The core check flow works without database credentials using the explainable MVP analysis route at `POST /api/analyse`. Production uses a managed Supabase PostgreSQL database with the FastAPI-owned authentication schema in `backend/migrations`; local development may use any local PostgreSQL instance.

The analysis route also works without Jev or PostgreSQL. In that mode it returns
an explainable local-rules result and clearly records that Jev was not used.

## Deploy on Vercel

The root `vercel.json` deploys two services in one Vercel project:

- `app`: the public Next.js service, routed at every public path.
- `backend`: the internal FastAPI service, called by `app` through the
  runtime-injected `BACKEND_URL` service binding.

Set the Vercel project's framework to **Services**, configure the backend's
`DATABASE_URL`, `JWT_SECRET`, and other secrets in the project environment, and
deploy normally. Do not create `BACKEND_URL` yourself; Vercel injects it from
the service binding. Run all services locally with `vercel dev`. When using
`npm run dev`, the same command starts the FastAPI server at
`http://127.0.0.1:8000` for `POST /api/analyse`.

## Local FastAPI and PostgreSQL backend

The local PostgreSQL migration is separate from the Supabase migration because
authentication is owned by FastAPI instead of `auth.users` and `auth.uid()`.

```bash
createdb guard                         # skip when the database already exists
psql -d guard -f backend/migrations/001_guard_postgres.sql
psql -d guard -f backend/migrations/002_analysis_signals.sql
psql -d guard -f backend/migrations/002_guard_intelligence.sql
psql -d guard -f backend/migrations/003_extended_detection_signals.sql
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # keep the real file private
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

You can also apply every outstanding migration with:

```bash
backend/.venv/bin/python backend/scripts/migrate.py
```

## Production database: managed Supabase Postgres

Use a Supabase project as the hosted PostgreSQL database for the deployed MVP.
Supabase is PostgreSQL, so the FastAPI application can keep its existing
SQLAlchemy models and Guard-owned authentication. Set the backend service's
`DATABASE_URL` to the Supabase **session pooler** connection string, set a unique
production `JWT_SECRET`, and run `backend/scripts/migrate.py` against that URL
once before the first deployment.

Git and GitHub contain the schema migrations, not the database or its records.
Pushing this repository therefore never uploads a local database. Local and
production databases are separate environments; migrations reproduce the
schema, while production records stay inside the Supabase project. Do not use
both the `supabase/migrations` schema and the `backend/migrations` schema for the
same database: this deployment uses `backend/migrations` because FastAPI owns
authentication.

To enable the optional Jev decision signal and database persistence, add these
settings to `backend/.env`:

```bash
JEV_API_KEY=your-server-side-key
JEV_BASE_URL=https://api.typesafe.ai
JEV_MODEL=jev-latest
JEV_TIMEOUT_SECONDS=5
ANALYSIS_PERSISTENCE_ENABLED=true
ANALYSIS_DATABASE_LOOKUP_ENABLED=true
STORE_ANALYSIS_CONTENT=false
```

Keep `STORE_ANALYSIS_CONTENT=false` unless raw messages have an approved
retention and access-control policy. Check records, hashes, results, evidence,
and provider metadata are still stored when raw-content storage is disabled.

Jev is a supporting signal. Guard's own risk engine owns the final score and
caps Jev's total contribution so that Jev alone cannot return `High Risk`.
Overlapping local and Jev indicators are deduplicated before scoring.

The API documentation is available at `http://127.0.0.1:8000/docs`. Authentication
routes are `POST /v1/auth/register`, `POST /v1/auth/login`, and the protected
`GET /v1/auth/me`. Login uses OAuth2 form fields: the email is sent as `username`
and the password as `password`.

## Partner public API

Guard now includes the first B2B2C API foundation for organizations that want
to protect their customers inside an existing product or workflow. The public
website exposes `POST /api/v1/checks`, which proxies to the FastAPI-owned
`POST /v1/checks` contract. Partner requests require a server-side Guard API
key; consumer JWTs and partner keys are deliberately separate credentials.

The partner API currently provides:

- Test and live API-key formats with one-time secret display and hashed storage.
- Organization status, plan, and monthly check quota enforcement.
- An optional `Idempotency-Key` header for safe network retries.
- Per-request IDs and an organization/key usage ledger for support and billing.
- The same explainable risk result used by Guard's web and Telegram channels.
- No automatic training-data contribution and no raw-content storage by default.

Apply `006_partner_public_api.sql`, configure a separate `API_KEY_PEPPER`, and
provision organizations and keys through the analyst-protected endpoints:

```text
POST /v1/admin/partners
GET  /v1/admin/partners
POST /v1/admin/partners/{organization_id}/keys
POST /v1/admin/partner-keys/{key_id}/revoke
```

In a Vercel deployment, the corresponding authenticated website proxies are
`/api/admin/partners`, `/api/admin/partners/{organization_id}/keys`, and
`/api/admin/partner-keys/{key_id}/revoke`.

The plaintext key is returned only by the key-creation response. Keep API keys
in a server-side secret manager; never embed them in browser or mobile code.
The public quickstart and request/response reference are available at
`/developers` on the website.

### Dashboard roles

Guard now routes each signed-in role to a dedicated workspace:

- `/dashboard` — personal user checks, reports, and safety activity.
- `/admin` — fraud analysts and super administrators operating Guard intelligence.
  Super administrators also see a Partners tab in the same dashboard sidebar for
  organization provisioning, membership, API-key, quota, and usage oversight.
- `/super-admin` — compatibility route that redirects to the unified admin dashboard.
- `/partner` — organization owners, admins, developers, and viewers monitoring
  their own API usage and risk outcomes in a full operational dashboard. Super
  administrators choose which workspace sections each organization can access;
  owners and partner admins can issue and revoke their organization's credentials.

Apply `007_partner_memberships.sql`, `008_partner_controls.sql`, and then
`009_partner_workspace_features.sql` after the public-API migration. A super
administrator can then attach an existing Guard user to an organization through
`POST /v1/admin/partners/{organization_id}/members`. Membership roles are
`owner`, `admin`, `developer`, and `viewer`.

The MVP API also exposes:

- `POST /v1/analyse` for all seven public analysis modes, with optional bearer
  authentication to attach a stored check to a user.
- `GET /v1/history` for a signed-in user's checks.
- `POST /v1/reports` for anonymous or signed-in report intake.
- `GET /v1/admin/checks` and `GET/PATCH /v1/admin/reports` for analyst review.
- `GET /health/live` for liveness and `GET /health` for database readiness.

## Telegram group fraud detection

The FastAPI service exposes `POST /api/integrations/telegram/webhook`. Vercel
routes that one public path directly to the backend service; the rest of the
public application remains on Next.js. Apply `005_telegram_integration.sql`
with `backend/.venv/bin/python backend/scripts/migrate.py`, then configure these
backend service environment variables:

```bash
TELEGRAM_BOT_TOKEN=token-from-botfather
TELEGRAM_WEBHOOK_SECRET=a-long-random-A-Za-z0-9_-value
TELEGRAM_ALLOWED_GROUP_IDS=-1001234567890,-1009876543210
TELEGRAM_TIMEOUT_SECONDS=5
```

Keep `ANALYSIS_PERSISTENCE_ENABLED=true` in production so detections appear in
the admin Fraud checks view. Telegram checks store a content hash, length,
source and delivery metadata; raw messages remain excluded while
`STORE_ANALYSIS_CONTENT=false`.

Create the bot with `@BotFather`, add it to the existing group, and either make
it an administrator or use `/setprivacy` in BotFather to disable privacy mode.
Telegram privacy mode otherwise limits bots to commands, replies, mentions and
service messages, so Guard would not receive ordinary group posts. The bot only
needs permission to view messages and send messages; deletion and member
management permissions are not required. If you change privacy mode, remove and
re-add the bot to the group so Telegram applies the new setting.

Register the webhook after the production deployment (replace the placeholders):

```bash
curl --fail-with-body -X POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://YOUR_GUARD_DOMAIN/api/integrations/telegram/webhook",
    "secret_token": "YOUR_TELEGRAM_WEBHOOK_SECRET",
    "allowed_updates": ["message"],
    "drop_pending_updates": true
  }'
```

Confirm registration with `getWebhookInfo`. To determine a group ID safely,
temporarily remove the webhook, post a test message in the group, call
`getUpdates`, and read `message.chat.id`; supergroup IDs are normally negative
and begin with `-100`. Restore the webhook immediately and put only approved IDs
in `TELEGRAM_ALLOWED_GROUP_IDS`.

For an end-to-end test, post a harmless sentence and confirm that Guard stays
silent. Then post a synthetic example such as “Urgent MoMo reversal: send your
OTP now” and confirm that Guard replies to that message. In Admin → Fraud
checks, verify the Telegram source, detection time, risk result, warning signs
and `delivered` alert state. Use a non-production test group first.

All seven public check modes use the same result contract. Message, payment,
call, and OCR-extracted screenshot text use the explainable text engine; links
also receive URL-shape and moderated reputation checks; phone and WhatsApp
numbers use verified reputation records and remain inconclusive when unknown.
Screenshot OCR runs in the browser, so the original image is not uploaded by
the check flow. The public endpoints include a per-instance rate-limit baseline;
use a shared edge or Redis limiter before scaling to multiple regions.

See `docs/backend-architecture.md` for the complete architecture, authentication
flow, database design, frontend integration examples, and production checklist.

Run the backend regression suite with:

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Generate a production JWT secret with `openssl rand -hex 32`; never reuse the
development secret or commit `backend/.env`.
Generate `API_KEY_PEPPER` separately with the same command. Rotating that value
invalidates existing partner keys, so manage it as a durable production secret.

## Product areas

- Public website: `/`, `/learn`, `/about`
- Detection experience: `/detect` and the six `/detect/[kind]` screens
- User dashboard shell: `/dashboard`
- Admin intelligence dashboard: `/admin`

## Intelligence pipeline

`POST /v1/analyse` is the shared analysis endpoint for the web app, future
browser/mobile clients and partner integrations. Private checks are not dataset
contributions. `POST /v1/contributions` requires explicit contribution consent
and creates a de-identified candidate in the human review queue.

Analyst-only routes under `/v1/intelligence` provide the overview, review
decisions, dataset filters, manual entry, CSV/XLSX/JSON imports, provenance,
brands, URL and phone intelligence. Imported and reported records remain pending
until an analyst marks them fraud, legitimate or uncertain and approves them.
Model and dataset version tables deliberately do not trigger automatic training.

After registering the first real administrator, promote that account once from a
trusted database session (replace the example email):

```sql
update profiles set role = 'super_admin'
where id = (select id from users where email = 'admin@example.com');
```

The hard-coded demo admin continues to show safe preview data; live Intelligence
writes require a real JWT-backed `super_admin` or `fraud_analyst` account.

## Security notes

Never expose `SUPABASE_SERVICE_ROLE_KEY` or `OPENAI_API_KEY` to the browser. Treat uploaded assets and submitted text as untrusted content, validate MIME and size server-side, and generate signed URLs for private evidence only.
# Guard-by-Bloomers
