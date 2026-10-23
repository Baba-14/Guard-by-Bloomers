begin;

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug varchar(80) not null unique,
  status text not null default 'active' check (status in ('active','suspended')),
  plan text not null default 'pilot',
  monthly_check_quota integer not null default 1000 check (monthly_check_quota >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.partner_api_keys (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  prefix varchar(48) not null unique,
  secret_hash char(64) not null unique,
  environment text not null default 'test' check (environment in ('test','live')),
  scopes jsonb not null default '["checks:write"]'::jsonb,
  last_used_at timestamptz,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.partner_api_usage (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  api_key_id uuid not null references public.partner_api_keys(id) on delete cascade,
  check_id uuid references public.checks(id) on delete set null,
  request_id uuid not null default gen_random_uuid() unique,
  idempotency_key varchar(160),
  endpoint text not null default '/v1/checks',
  response_status integer not null,
  response_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint partner_usage_org_idempotency_key unique (organization_id, idempotency_key)
);

create index partner_api_keys_organization_id_idx on public.partner_api_keys(organization_id);
create index partner_api_usage_organization_created_idx on public.partner_api_usage(organization_id, created_at desc);
create index partner_api_usage_key_created_idx on public.partner_api_usage(api_key_id, created_at desc);

create trigger set_organizations_updated_at before update on public.organizations
for each row execute function public.set_updated_at();
create trigger set_partner_api_keys_updated_at before update on public.partner_api_keys
for each row execute function public.set_updated_at();

commit;
