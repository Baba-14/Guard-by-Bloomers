-- Guard local PostgreSQL schema.
-- This is the local equivalent of supabase/migrations/001_guard_schema.sql.
-- Authentication and authorization are owned by FastAPI, so Supabase auth.users,
-- auth.uid(), and row-level policies are intentionally replaced by public.users.

begin;

create extension if not exists pgcrypto;

create type public.user_role as enum ('user','super_admin','fraud_analyst','support_admin');
create type public.risk_level as enum ('low','caution','high','unable_to_determine');
create type public.report_status as enum ('submitted','under_review','verified_signal','insufficient_evidence','rejected','appealed','archived');

create table public.users (
  id uuid primary key default gen_random_uuid(),
  email varchar(320) not null unique,
  password_hash text not null,
  is_active boolean not null default true,
  email_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references public.users(id) on delete cascade,
  full_name text,
  role public.user_role not null default 'user',
  privacy_preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.fraud_categories (
  id uuid primary key default gen_random_uuid(), name text not null unique,
  slug text not null unique, description text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.fraud_signals (
  id uuid primary key default gen_random_uuid(), key text not null unique,
  name text not null, weight integer not null default 10,
  severity text not null default 'medium', active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete set null,
  check_type text not null, input_metadata jsonb not null default '{}'::jsonb,
  status text not null default 'submitted', is_saved boolean not null default false,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.analysis_results (
  id uuid primary key default gen_random_uuid(),
  check_id uuid not null unique references public.checks(id) on delete cascade,
  risk_level public.risk_level not null, risk_score integer check (risk_score between 0 and 100),
  likely_pattern text, explanation text, recommended_action text,
  model_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.uploaded_assets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references public.profiles(id) on delete set null,
  check_id uuid references public.checks(id) on delete cascade,
  bucket text not null, object_path text not null, mime_type text not null,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0), retention_until timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (bucket, object_path)
);
create table public.check_signals (
  check_id uuid references public.checks(id) on delete cascade,
  signal_id uuid references public.fraud_signals(id) on delete cascade,
  evidence text, weight_applied integer,
  primary key (check_id, signal_id)
);
create table public.fraud_patterns (
  id uuid primary key default gen_random_uuid(), name text not null,
  description text, category_id uuid references public.fraud_categories(id) on delete set null,
  severity text, status text not null default 'active',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.phone_entities (
  id uuid primary key default gen_random_uuid(), normalized_number text not null unique,
  country_code text not null default 'GH',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.domain_entities (
  id uuid primary key default gen_random_uuid(), domain text not null unique,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.payment_entities (
  id uuid primary key default gen_random_uuid(), identifier text not null unique, provider text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.social_entities (
  id uuid primary key default gen_random_uuid(), handle text not null, platform text not null,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (platform, handle)
);
create table public.fraud_reports (
  id uuid primary key default gen_random_uuid(),
  reporter_id uuid references public.profiles(id) on delete set null,
  category_id uuid references public.fraud_categories(id) on delete set null,
  status public.report_status not null default 'submitted', description text not null,
  entity_type text, entity_value text, amount_requested numeric check (amount_requested is null or amount_requested >= 0),
  amount_lost numeric check (amount_lost is null or amount_lost >= 0), incident_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.fraud_report_evidence (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.fraud_reports(id) on delete cascade,
  bucket text not null default 'fraud-report-evidence', object_path text not null, mime_type text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (bucket, object_path)
);
create table public.entity_relationships (
  id uuid primary key default gen_random_uuid(), from_type text not null, from_id uuid not null,
  relationship text not null, to_type text not null, to_id uuid not null,
  confidence numeric not null default 1 check (confidence between 0 and 1),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (from_type, from_id, relationship, to_type, to_id)
);
create table public.reputation_scores (
  id uuid primary key default gen_random_uuid(), entity_type text not null, entity_id uuid not null,
  report_count integer not null default 0 check (report_count >= 0),
  independent_reporters integer not null default 0 check (independent_reporters >= 0),
  evidence_count integer not null default 0 check (evidence_count >= 0),
  score integer not null default 0 check (score between 0 and 100), moderated boolean not null default false,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (entity_type, entity_id)
);
create table public.feedback (
  id uuid primary key default gen_random_uuid(), user_id uuid references public.profiles(id) on delete set null,
  check_id uuid references public.checks(id) on delete cascade, helpful boolean, comment text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.appeals (
  id uuid primary key default gen_random_uuid(), report_id uuid not null references public.fraud_reports(id) on delete cascade,
  user_id uuid references public.profiles(id) on delete set null, reason text not null,
  status text not null default 'submitted',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.education_content (
  id uuid primary key default gen_random_uuid(), slug text unique not null, title text not null,
  body jsonb not null default '{}'::jsonb, published boolean not null default false,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.admin_notes (
  id uuid primary key default gen_random_uuid(), admin_id uuid references public.profiles(id) on delete set null,
  report_id uuid not null references public.fraud_reports(id) on delete cascade, note text not null,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.audit_logs (
  id uuid primary key default gen_random_uuid(), actor_id uuid references public.profiles(id) on delete set null,
  action text not null, target_type text, target_id uuid, metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create index checks_user_id_idx on public.checks(user_id);
create index checks_created_at_idx on public.checks(created_at desc);
create index fraud_reports_reporter_id_idx on public.fraud_reports(reporter_id);
create index fraud_reports_status_idx on public.fraud_reports(status);
create index fraud_reports_created_at_idx on public.fraud_reports(created_at desc);
create index audit_logs_actor_id_idx on public.audit_logs(actor_id);
create index audit_logs_created_at_idx on public.audit_logs(created_at desc);

create function public.set_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

do $$
declare table_name text;
begin
  foreach table_name in array array[
    'users','profiles','fraud_categories','fraud_signals','checks','analysis_results',
    'uploaded_assets','fraud_patterns','phone_entities','domain_entities','payment_entities',
    'social_entities','fraud_reports','fraud_report_evidence','entity_relationships',
    'reputation_scores','feedback','appeals','education_content','admin_notes','audit_logs'
  ] loop
    execute format(
      'create trigger set_%I_updated_at before update on public.%I for each row execute function public.set_updated_at()',
      table_name, table_name
    );
  end loop;
end;
$$;

insert into public.fraud_signals (key,name,weight,severity) values
 ('otp_request','OTP Request',35,'high'),
 ('pin_request','PIN Request',45,'critical'),
 ('password_request','Password Request',35,'high'),
 ('urgency','Urgency',10,'medium'),
 ('fear_or_threat','Fear or Threat',18,'high'),
 ('advance_payment','Advance Payment',25,'high'),
 ('guaranteed_return','Guaranteed Return',25,'high'),
 ('suspicious_domain','Suspicious URL',25,'high'),
 ('impersonation','Impersonation',25,'high'),
 ('remote_access_request','Remote Access Request',40,'critical');

commit;
