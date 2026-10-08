# Guard

Guard is a Ghana-first fraud-prevention and fraud-intelligence MVP.

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

Development uses `.next`; production builds use `.next-build`, so running a build will not invalidate an active development server. Do not run two `next dev` processes against the same port.

The core check flow works without Supabase credentials using the explainable MVP analysis route at `POST /api/analyse`. The Supabase migration in `supabase/migrations/001_guard_schema.sql` remains available for a Supabase deployment. Local development uses the FastAPI-owned authentication and PostgreSQL migration described below.

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
`npm run dev` instead, `POST /api/analyse` falls back to a FastAPI server at
`http://127.0.0.1:8000`.

## Local FastAPI and PostgreSQL backend

The local PostgreSQL migration is separate from the Supabase migration because
authentication is owned by FastAPI instead of `auth.users` and `auth.uid()`.

```bash
createdb guard                         # skip when the database already exists
psql -d guard -f backend/migrations/001_guard_postgres.sql
psql -d guard -f backend/migrations/002_analysis_signals.sql
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # keep the real file private
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

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

The completed MVP API also exposes:

- `POST /v1/analyse` for public message and URL analysis, with optional bearer
  authentication to attach a stored check to a user.
- `GET /v1/history` for a signed-in user's checks.
- `POST /v1/reports` for anonymous or signed-in report intake.
- `GET /v1/admin/checks` and `GET/PATCH /v1/admin/reports` for analyst review.
- `GET /health/live` for liveness and `GET /health` for database readiness.

See `docs/backend-architecture.md` for the complete architecture, authentication
flow, database design, frontend integration examples, and production checklist.

Run the backend regression suite with:

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Generate a production JWT secret with `openssl rand -hex 32`; never reuse the
development secret or commit `backend/.env`.

## Product areas

- Public website: `/`, `/learn`, `/about`
- Detection experience: `/detect` and the six `/detect/[kind]` screens
- User dashboard shell: `/dashboard`
- Admin intelligence dashboard: `/admin`

## Security notes

Never expose `SUPABASE_SERVICE_ROLE_KEY` or `OPENAI_API_KEY` to the browser. Treat uploaded assets and submitted text as untrusted content, validate MIME and size server-side, and generate signed URLs for private evidence only.
# Guard-by-Bloomers
