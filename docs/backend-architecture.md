# Guard Backend and Database Architecture

This document explains what has been implemented, why each technology is used,
how a request moves through the system, and how the Next.js frontend can connect
to the FastAPI backend.

## 1. Current system at a glance

```text
Browser
  |
  | HTTP/JSON and Bearer access tokens
  v
Next.js frontend (localhost:3000)
  |
  | HTTP API requests
  v
FastAPI backend (localhost:8000)
  |
  | SQLAlchemy + Psycopg
  v
Local PostgreSQL: guard
```

The browser-facing application is Next.js. FastAPI owns backend validation,
authentication, authorization, and fraud-analysis endpoints. PostgreSQL is the
system of record for users and Guard data.

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

The local database is named `guard`.

### SQLAlchemy

SQLAlchemy is the Python database layer. It creates the connection engine,
provides request-scoped sessions, and maps Python objects to database tables.

The current ORM models cover `users` and `profiles`, which are required for
authentication. The rest of the tables already exist in PostgreSQL and can be
mapped as their API features are implemented.

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

### Alembic status

Alembic was discussed as the long-term migration tool, but it has **not been
configured yet**. The schema currently uses a plain SQL migration:

```text
backend/migrations/001_guard_postgres.sql
```

That migration has already been applied to the local `guard` database. Alembic
should be introduced before the project starts accumulating many incremental
schema changes. Until then, the SQL file is the local schema source of truth.

### Uvicorn

Uvicorn is the development/application server that runs FastAPI.

```bash
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

## 3. Database architecture

The Supabase schema was preserved at
`supabase/migrations/001_guard_schema.sql`. A local PostgreSQL version was
created at `backend/migrations/001_guard_postgres.sql`.

The important translation is:

```text
Supabase auth.users        -> public.users
Supabase auth.uid() / RLS  -> FastAPI authentication and authorization
uuid_generate_v4()         -> gen_random_uuid()
```

The original Supabase migration was not overwritten, so a future Supabase
deployment remains possible.

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
Frontend sends Authorization: Bearer <token>
  -> FastAPI verifies JWT signature and expiry
  -> FastAPI loads the current user from PostgreSQL
  -> inactive or missing users receive 401
  -> valid users reach the protected route
```

`GET /v1/auth/me` is the current example of a protected route.

## 5. Current API surface

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Confirms API and database availability |
| `POST` | `/v1/auth/register` | No | Creates a user and profile |
| `POST` | `/v1/auth/login` | No | Verifies credentials and issues a JWT |
| `GET` | `/v1/auth/me` | Bearer JWT | Returns the current user |
| `POST` | `/v1/analyse` | No | Runs deterministic fraud analysis |

The interactive version is available at `http://127.0.0.1:8000/docs` while the
backend is running.

## 6. Connecting the Next.js frontend

### Step 1: configure the API URL

Add this to the root `.env.local` file used by Next.js:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Restart `npm run dev` after changing an environment file.

The backend currently allows browser requests from `http://localhost:3000` via
CORS. If Next.js uses a different origin, update `CORS_ORIGINS` in
`backend/.env` and restart FastAPI.

### Step 2: create a frontend API helper

A helper such as `lib/api.ts` can centralize the backend address and error
handling:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

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
  return parseResponse(await fetch(`${API_URL}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }));
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  return parseResponse(await fetch(`${API_URL}/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  }));
}

export async function getCurrentUser(accessToken: string) {
  return parseResponse(await fetch(`${API_URL}/v1/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  }));
}
```

### Step 3: replace demo login

The current login page compares credentials against hard-coded demo accounts.
Replace that comparison with `login(email, password)`.

For the first frontend integration, the returned token can be placed in
`sessionStorage`:

```ts
const result = await login(email, password);
sessionStorage.setItem('guard-access-token', result.access_token);
sessionStorage.setItem('guard-user', JSON.stringify(result.user));
router.push(result.user.role === 'user' ? '/dashboard' : '/admin');
```

This matches the current bearer-token backend and is acceptable for local MVP
development. For production, an HTTP-only, secure, same-site cookie managed by
a server route is preferable because browser JavaScript cannot read it, which
reduces token theft through cross-site scripting.

### Step 4: connect registration

Convert the registration page to a client component with controlled name,
email, and password inputs. Call `register(...)`, display validation/API errors,
then either send the user to login or log them in immediately.

### Step 5: protect dashboard requests

When the dashboard loads, read the token and call `/v1/auth/me`. If the token is
missing, expired, or invalid, clear the session and redirect to `/login`.

Frontend redirects improve the experience, but they are not security controls.
Every sensitive FastAPI endpoint must still validate the JWT and enforce roles.

### Step 6: connect fraud analysis

The frontend currently calls the Next.js route `/api/analyse`. It can instead
call FastAPI at `${NEXT_PUBLIC_API_URL}/v1/analyse`.

Note the current request-property difference:

```text
Next.js route uses: input
FastAPI route uses: content
```

The frontend should send:

```json
{
  "kind": "message",
  "content": "The message to analyse"
}
```

The response naming also differs: FastAPI returns `explanation` and
`recommended_action`, while the current Next.js UI expects `reason` and
`action`. These contracts should be standardized when the frontend is wired in.

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
- Persist fraud checks and analysis results from `/v1/analyse`.
- Add role-check dependencies and protected admin endpoints.
- Add email verification.
- Add password reset and password change flows.
- Decide on refresh tokens or shorter cookie-backed sessions.
- Add logout/token revocation if refresh tokens are introduced.
- Add login rate limiting and account lockout protections.
- Add audit logging for authentication and administrative actions.
- Add evidence file validation and private object storage.
- Add automated API and database tests.
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

1. Standardize the FastAPI and frontend fraud-analysis request/response types.
2. Create `lib/api.ts` and connect registration.
3. Connect login and `/v1/auth/me`.
4. Add a reusable frontend auth provider and route guards.
5. Persist authenticated checks and results.
6. Add server-side role enforcement for admin APIs.
7. Introduce Alembic before making the next database schema change.

