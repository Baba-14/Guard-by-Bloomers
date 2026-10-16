# Guard Backend and Database Architecture

This document explains what has been implemented, why each technology is used,
how a request moves through the system, and how the Next.js frontend can connect
to the FastAPI backend.

## 1. Current system at a glance

```text
Browser
  |
  | HTTP/JSON and HTTP-only session cookie
  v
Next.js frontend (localhost:3000)
  |
  | HTTP API requests
  v
FastAPI backend (local or deployed service)
  |
  | SQLAlchemy + Psycopg
  v
PostgreSQL (local development or managed Supabase in production)
```

The browser-facing application is Next.js. FastAPI owns backend validation,
authentication, authorization, and fraud-analysis endpoints. PostgreSQL is the
system of record for users and Guard data.

### Fraud-decision architecture

Infrastructure and database design do not decide whether something is risky.
Guard's analysis pipeline makes that boundary explicit:

```text
Message, screenshot text, link, number, WhatsApp, payment, or call
      |
      v
Validation and normalization
      |
      +------------------+------------------+------------------+
      v                  v                  v                  v
Behavior rules      URL-shape checks   Guard reputation   Jev typed questions
      |                  |                  |                  |
      +------------------+------------------+------------------+
                         v
                  Guard risk engine
                  - deduplicate evidence
                  - cap AI contribution
                  - apply Guard thresholds
                         |
                         v
        Classification + reasons + safer action
                         |
                         v
             Optional PostgreSQL persistence
```

The modules live under `backend/app/analysis/`:

- `rules.py`: deterministic, word-boundary-aware message signals.
- `urls.py`: local URL structure and deception signals.
- `knowledge.py`: verified Guard URL, domain, phone, and WhatsApp reputation evidence.
- `jev.py`: timeout-bounded Jev adapter and typed questions.
- `engine.py`: Guard-owned score fusion and output language.
- `persistence.py`: optional check, result, and evidence storage.

Jev never owns the final verdict. Its combined contribution is capped at 30
points while `High Risk` starts at 55. The route continues with local analysis
when no key is configured or when Jev times out or fails.

## 2. Technology stack

### FastAPI

FastAPI is the Python web API framework. It provides:

- HTTP route handling.
- Request validation through Pydantic.
- Dependency injection for database sessions and authenticated users.
- Generated OpenAPI documentation at `/docs`.
- Consistent HTTP responses and status codes.

The application entry point is `backend/app/main.py`.

### PostgreSQL

PostgreSQL is the database. It was chosen instead of SQLite because Guard needs:

- Concurrent users and writes.
- Strong foreign-key and unique constraints.
- UUID primary keys.
- JSONB metadata.
- Enums for roles, risk levels, and report statuses.
- Reliable reporting and aggregation as fraud data grows.

The default local database is named `guard`; production uses a managed
Supabase PostgreSQL project through its session pooler.

### SQLAlchemy

SQLAlchemy is the Python database layer. It creates the connection engine,
provides request-scoped sessions, and maps Python objects to database tables.

The ORM models cover authentication, checks and results, signal links, domain
reputation, fraud reports, and audit logs. Other schema tables remain available
to map as their product features are implemented.

Relevant files:

- `backend/app/database.py`: engine and session factory.
- `backend/app/models.py`: `User`, `Profile`, and `UserRole` mappings.

### Psycopg

Psycopg is the PostgreSQL driver used underneath SQLAlchemy. SQLAlchemy builds
queries and manages sessions; Psycopg performs the actual communication with
PostgreSQL.

### Pydantic

Pydantic validates incoming and outgoing API data. Examples include:

- Checking that an email is structurally valid.
- Requiring passwords to contain between 8 and 128 characters.
- Limiting names and fraud-analysis input sizes.
- Ensuring API responses use the documented structure.

Pydantic validation happens before route logic is executed. Invalid requests
normally receive HTTP `422`.

### Argon2

Argon2 is the password-hashing algorithm used through `pwdlib`.

Passwords are never stored directly. Registration performs this transformation:

```text
plain password -> Argon2 password hash -> users.password_hash
```

During login, the submitted password is verified against the stored hash. A
hash cannot be converted back into the original password.

### JWT

JWT provides signed access tokens. After a valid login, FastAPI signs a token
containing:

- `sub`: the user's UUID.
- `role`: the user's role when the token was issued.
- `exp`: the token expiry time.

The current token lifetime is 60 minutes. A protected request supplies it as:

```http
Authorization: Bearer <access-token>
```

FastAPI verifies the signature and expiry, extracts the user ID, and loads the
current user from PostgreSQL. Disabled or deleted users are rejected even if an
older token still exists.

### Migration status

Alembic has **not been configured yet**. The schema currently uses ordered SQL
migrations under:

```text
backend/migrations/*.sql
```

`backend/scripts/migrate.py` records applied filenames in
`guard_schema_migrations` and can target local PostgreSQL or Supabase. Alembic
should be introduced before migration branching becomes frequent.

### Uvicorn

Uvicorn is the development/application server that runs FastAPI.

```bash
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

## 3. Database architecture

The production schema source of truth is `backend/migrations`. It works against
both local PostgreSQL and a managed Supabase PostgreSQL database.

The important translation is:

```text
Supabase auth.users        -> public.users
Supabase auth.uid() / RLS  -> FastAPI authentication and authorization
uuid_generate_v4()         -> gen_random_uuid()
```

The older `supabase/migrations` tree represents a Supabase-Auth/RLS alternative
and must not be applied to the same database as `backend/migrations`.

The additive Guard Intelligence schema is in `backend/migrations/002_guard_intelligence.sql`
and `supabase/migrations/002_guard_intelligence.sql`. It adds provenance-aware
dataset items and sources, review queue decisions, brands, URL/phone intelligence,
model predictions, and dataset/model versions while continuing to reference the
existing `fraud_reports`, `checks`, `fraud_categories`, `phone_entities`, and
`domain_entities` tables.

Private analysis and data contribution are intentionally separate:

```text
POST /v1/analyse -> fused risk result -> optional hash/result persistence
POST /v1/contributions -> consented report -> de-identification -> pending review
pending review -> analyst decision -> verified dataset
verified dataset -> explicit dataset version/split -> offline evaluation/training
```

There is no route or database trigger that trains or deploys a model from pending
or newly verified records.

### Authentication tables

`users` contains security-related account data:

- Unique email address.
- Argon2 password hash.
- Active/disabled status.
- Email-verification status.
- Creation and update timestamps.

`profiles` contains application-facing identity data:

- The same UUID as its related user.
- Full name.
- Role.
- Privacy preferences.

Separating authentication data from profile data limits how much security data
ordinary application queries need to touch.

### Fraud-check tables

- `checks`: each submitted fraud check and its metadata.
- `analysis_results`: risk level, score, explanation, and recommendation.
- `fraud_signals`: reusable weighted warning signals.
- `check_signals`: signals associated with a specific check.
- `uploaded_assets`: metadata for screenshots or uploaded evidence.

### Reporting and intelligence tables

- `fraud_reports`: user-submitted fraud reports.
- `fraud_report_evidence`: evidence associated with reports.
- `fraud_categories`: standardized fraud categories.
- `fraud_patterns`: known fraud patterns.
- `phone_entities`, `domain_entities`, `payment_entities`, `social_entities`:
  normalized entities involved in reports.
- `entity_relationships`: graph-style connections between entities.
- `reputation_scores`: aggregate risk/reputation values for entities.

### Operations tables

- `feedback`: whether analysis was helpful.
- `appeals`: challenges to report decisions.
- `education_content`: fraud-awareness content.
- `admin_notes`: internal moderation notes.
- `audit_logs`: sensitive administrative activity history.

Foreign keys define ownership and cleanup behavior. For example, deleting a
check also deletes its analysis result, while deleting a user preserves many
fraud records by setting their user reference to `NULL`.

Database constraints provide a second validation layer. They enforce unique
emails, risk scores between 0 and 100, non-negative amounts and counters, and
valid confidence values.

## 4. Authentication flow

### Registration

```text
Frontend
  -> POST /v1/auth/register with JSON
FastAPI
  -> validates name, email, and password
  -> normalizes the email
  -> checks for an existing account
  -> hashes the password with Argon2
  -> inserts users and profiles in one transaction
  -> returns safe user data without the password hash
```

Example request:

```json
{
  "email": "ama@example.com",
  "password": "a-strong-password",
  "full_name": "Ama Mensah"
}
```

### Login

The login endpoint follows the OAuth2 password form convention, so it receives
URL-encoded form data rather than JSON. The email goes into the `username`
field.

```text
Frontend
  -> POST /v1/auth/login
FastAPI
  -> looks up the normalized email
  -> verifies the password against the Argon2 hash
  -> checks that the account is active
  -> signs a JWT
  -> returns the token, expiry, and user data
```

### Protected requests

```text
Browser sends the HTTP-only Guard session cookie to the Next.js API route
  -> Next.js forwards Authorization: Bearer <token> to FastAPI
  -> FastAPI verifies JWT signature and expiry
  -> FastAPI loads the current user from PostgreSQL
  -> inactive or missing users receive 401
  -> valid users reach the protected route
```

`GET /v1/auth/me`, `GET /v1/history`, and the analyst routes are protected.

## 5. Current API surface

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Confirms API and database availability |
| `GET` | `/health/live` | No | Confirms the API process is responsive |
| `POST` | `/v1/auth/register` | No | Creates a user and profile |
| `POST` | `/v1/auth/login` | No | Verifies credentials and issues a JWT |
| `GET` | `/v1/auth/me` | Bearer JWT | Returns the current user |
| `POST` | `/v1/analyse` | Optional JWT | Runs Guard rules, URL and database checks, optional Jev, and score fusion |
| `GET` | `/v1/history` | Bearer JWT | Returns the current user's stored checks |
| `POST` | `/v1/reports` | Optional JWT | Accepts an anonymous or owned fraud report |
| `GET` | `/v1/admin/checks` | Analyst/admin JWT | Reviews recent stored checks |
| `GET` | `/v1/admin/reports` | Analyst/admin JWT | Lists the report review queue |
| `PATCH` | `/v1/admin/reports/{id}` | Analyst/admin JWT | Changes report status and writes an audit log |

The interactive version is available at `http://127.0.0.1:8000/docs` while the
backend is running.

## 6. Connecting the Next.js frontend

### Step 1: use the same-origin Next.js API

The browser calls `POST /api/analyse` on the same origin. That Next.js route runs
at request time and calls FastAPI through the `BACKEND_URL` Vercel service
binding. Vercel injects the binding; do not add `BACKEND_URL` to project
environment variables.

With `npm run dev`, the server route falls back to `http://127.0.0.1:8000`, so
run FastAPI locally as described above. `vercel dev` runs both services and
provides the binding automatically.

### Step 2: create a frontend API helper

A helper such as `lib/api.ts` can centralize the backend address and error
handling:

```ts
const API_URL = '/api';

async function parseResponse(response: Response) {
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.detail ?? 'Request failed');
  }
  return body;
}

export async function register(input: {
  full_name: string;
  email: string;
  password: string;
}) {
  return parseResponse(await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }));
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  return parseResponse(await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  }));
}

export async function getCurrentUser(accessToken: string) {
  return parseResponse(await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  }));
}
```

### Step 3: production login

The login page calls the same-origin Next.js authentication route. That route
exchanges credentials with FastAPI and stores the JWT in an HTTP-only, secure,
same-site cookie. Browser JavaScript never receives the token:

```ts
const result = await login(email, password); // cookie is set by the server route
router.push(result.user.role === 'user' ? '/dashboard' : '/admin');
```

Demo accounts are available only when `NEXT_PUBLIC_ENABLE_DEMO_AUTH=true`; keep
that variable false or unset in production.

### Step 4: connect registration

The registration page uses controlled inputs, displays validation/API errors,
logs the new user in, and redirects to the dashboard.

### Step 5: protect dashboard requests

When the dashboard loads, call `/api/auth/me`. If the cookie is missing, expired,
or invalid, redirect to `/login`.

Frontend redirects improve the experience, but they are not security controls.
Every sensitive FastAPI endpoint must still validate the JWT and enforce roles.

### Step 6: connect fraud analysis

The frontend calls the Next.js route `/api/analyse`, which adapts the public
request and response shape to FastAPI's internal `/v1/analyse` endpoint.

Note the current request-property difference:

```text
Next.js route uses: input
FastAPI route uses: content
```

The frontend should send:

```json
{
  "kind": "message",
  "input": "The message to analyse"
}
```

The Next.js route translates `input` to FastAPI's internal `content` property
and maps FastAPI's `explanation` and `recommended_action` fields to the UI's
`reason` and `action` fields.

## 7. Security requirements already considered

- Passwords are hashed with Argon2 and never returned by the API.
- JWT signing requires a secret containing at least 32 characters.
- Access tokens expire.
- Protected routes reload the user and reject disabled accounts.
- Emails are normalized and unique.
- Request sizes and formats have application-level limits.
- PostgreSQL constraints protect data even if application validation is missed.
- The database URL and JWT secret live in the ignored `backend/.env` file.
- CORS is restricted to configured frontend origins.
- Uploaded or submitted fraud content is treated as untrusted data.

## 8. Work still required before production

The foundation works, but the following features have not been implemented yet:

- Connect the Next.js login and registration forms to FastAPI.
- Associate optionally authenticated users with their fraud checks.
- Connect the existing admin interface to the protected recent-checks endpoint.
- Add email verification.
- Add password reset and password change flows.
- Decide on refresh tokens or shorter cookie-backed sessions.
- Add logout/token revocation if refresh tokens are introduced.
- Add login rate limiting and account lockout protections.
- Add audit logging for authentication and administrative actions.
- Add evidence file validation and private object storage.
- Add database integration tests in addition to the risk-engine regression suite.
- Configure Alembic for future incremental migrations.
- Replace the development JWT secret before any deployment.
- Deploy PostgreSQL and FastAPI behind TLS/HTTPS.

## 9. Local development commands

Start FastAPI:

```bash
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

Start Next.js in a separate terminal:

```bash
npm run dev
```

Check the backend/database connection:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","database":"connected"}
```

## 10. Recommended next implementation order

1. Build and review the Ghana-focused labelled evaluation set in `DATA.md`.
2. Measure local-only and local-plus-Jev results against the same examples.
3. Add a dedicated URL-reputation provider behind the URL analyzer boundary.
4. Connect login, registration, and authenticated check ownership.
5. Connect the admin interface to `/v1/admin/checks`.
6. Introduce Alembic before making the next database schema change.
