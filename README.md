# Guard

Guard is a Ghana-first fraud-prevention and fraud-intelligence MVP.

## Run locally

```bash
npm install
cp .env.example .env.local
npm run dev
```

Development uses `.next`; production builds use `.next-build`, so running a build will not invalidate an active development server. Do not run two `next dev` processes against the same port.

The core check flow works without Supabase credentials using the deterministic MVP analysis route at `POST /api/analyse`. The Supabase migration in `supabase/migrations/001_guard_schema.sql` defines the production data model, storage-facing tables and baseline RLS policies. Add Supabase Auth and server-only service-role operations behind route handlers before production launch.

## Product areas

- Public website: `/`, `/learn`, `/about`
- Detection experience: `/detect` and the six `/detect/[kind]` screens
- User dashboard shell: `/dashboard`
- Admin intelligence dashboard: `/admin`

## Security notes

Never expose `SUPABASE_SERVICE_ROLE_KEY` or `OPENAI_API_KEY` to the browser. Treat uploaded assets and submitted text as untrusted content, validate MIME and size server-side, and generate signed URLs for private evidence only.
# Guard-by-Bloomers
