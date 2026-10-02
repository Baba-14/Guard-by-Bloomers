# Guard

Guard is a Ghana-first fraud-prevention and fraud-intelligence MVP.

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

Development uses `.next`; production builds use `.next-build`, so running a build will not invalidate an active development server. Do not run two `next dev` processes against the same port.

The core check flow works without Supabase credentials using the deterministic MVP analysis route at `POST /api/analyse`. The Supabase migration in `supabase/migrations/001_guard_schema.sql` remains available for a Supabase deployment. Local development uses the FastAPI-owned authentication and PostgreSQL migration described below.

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
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # keep the real file private
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`. Authentication
routes are `POST /v1/auth/register`, `POST /v1/auth/login`, and the protected
`GET /v1/auth/me`. Login uses OAuth2 form fields: the email is sent as `username`
and the password as `password`.

See `docs/backend-architecture.md` for the complete architecture, authentication
flow, database design, frontend integration examples, and production checklist.

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
