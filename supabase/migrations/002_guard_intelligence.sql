-- Guard Intelligence pipeline. Apply after 001_guard_postgres.sql.
begin;

create type public.dataset_label as enum ('fraud','legitimate','uncertain');
create type public.review_status as enum ('pending','in_review','verified','rejected');
create type public.dataset_source_type as enum (
  'public_dataset','user_report','partner','authoritative_pattern','synthetic','manual'
);

alter table public.fraud_reports
  add column explicit_contribution_consent boolean not null default false,
  add column consent_version text,
  add column privacy_status text not null default 'pending_deidentification';

create table public.dataset_sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source_type public.dataset_source_type not null,
  description text,
  source_uri text,
  license_name text,
  is_authoritative boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table public.brands (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  country_code char(2) not null default 'GH',
  official_domains jsonb not null default '[]'::jsonb,
  official_sender_ids jsonb not null default '[]'::jsonb,
  verified boolean not null default false,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table public.dataset_items (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  content_hash char(64) not null unique,
  content_type text not null default 'message',
  channel text,
  label public.dataset_label not null default 'uncertain',
  category_id uuid references public.fraud_categories(id) on delete set null,
  brand_id uuid references public.brands(id) on delete set null,
  source_id uuid not null references public.dataset_sources(id),
  fraud_report_id uuid unique references public.fraud_reports(id) on delete set null,
  country_code char(2),
  is_ghana_specific boolean not null default false,
  language text,
  verification_status public.review_status not null default 'pending',
  contribution_consent boolean not null default false,
  privacy_status text not null default 'pending_deidentification',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table public.review_queue (
  id uuid primary key default gen_random_uuid(),
  dataset_item_id uuid not null unique references public.dataset_items(id) on delete cascade,
  status public.review_status not null default 'pending',
  assigned_to uuid references public.profiles(id) on delete set null,
  reviewed_by uuid references public.profiles(id) on delete set null,
  decision public.dataset_label,
  category_id uuid references public.fraud_categories(id) on delete set null,
  notes text,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table public.labels (
  id uuid primary key default gen_random_uuid(), name text not null unique,
  description text, created_at timestamptz not null default now()
);
create table public.dataset_item_labels (
  dataset_item_id uuid references public.dataset_items(id) on delete cascade,
  label_id uuid references public.labels(id) on delete cascade,
  primary key (dataset_item_id,label_id)
);

create table public.dataset_versions (
  id uuid primary key default gen_random_uuid(),
  name text not null, version text not null, status text not null default 'draft', notes text,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(), unique(name,version)
);
create table public.dataset_version_items (
  dataset_version_id uuid references public.dataset_versions(id) on delete cascade,
  dataset_item_id uuid references public.dataset_items(id) on delete restrict,
  split text not null check (split in ('train','validation','test','holdout')),
  primary key(dataset_version_id,dataset_item_id)
);

create table public.model_versions (
  id uuid primary key default gen_random_uuid(), name text not null, version text not null,
  status text not null default 'candidate', artifact_uri text, metrics jsonb not null default '{}'::jsonb,
  training_dataset_version_id uuid references public.dataset_versions(id) on delete set null,
  created_at timestamptz not null default now(), unique(name,version)
);
create table public.model_predictions (
  id uuid primary key default gen_random_uuid(),
  model_version_id uuid references public.model_versions(id) on delete set null,
  check_id uuid references public.checks(id) on delete cascade,
  dataset_item_id uuid references public.dataset_items(id) on delete cascade,
  predicted_label public.dataset_label not null,
  confidence numeric check (confidence is null or confidence between 0 and 1),
  signals jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (check_id is not null or dataset_item_id is not null)
);

alter table public.feedback
  add column model_prediction_id uuid references public.model_predictions(id) on delete set null,
  add column corrected_label public.dataset_label,
  add column contribution_consent boolean not null default false;

create table public.url_intelligence (
  id uuid primary key default gen_random_uuid(), url text not null, normalized_url text not null unique,
  domain_id uuid references public.domain_entities(id) on delete set null,
  brand_id uuid references public.brands(id) on delete set null,
  source_id uuid references public.dataset_sources(id) on delete set null,
  verdict public.dataset_label not null default 'uncertain', risk_score integer not null default 0 check(risk_score between 0 and 100),
  report_count integer not null default 0 check(report_count >= 0), verified boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table public.phone_intelligence (
  id uuid primary key default gen_random_uuid(),
  phone_entity_id uuid unique references public.phone_entities(id) on delete cascade,
  sender_id text, brand_id uuid references public.brands(id) on delete set null,
  source_id uuid references public.dataset_sources(id) on delete set null,
  verdict public.dataset_label not null default 'uncertain', risk_score integer not null default 0 check(risk_score between 0 and 100),
  report_count integer not null default 0 check(report_count >= 0), verified boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  check (phone_entity_id is not null or sender_id is not null)
);

create index dataset_items_review_idx on public.dataset_items(verification_status,created_at desc);
create index dataset_items_filter_idx on public.dataset_items(label,is_ghana_specific,source_id);
create index review_queue_status_idx on public.review_queue(status,created_at);
create index url_intelligence_risk_idx on public.url_intelligence(risk_score desc);
create index phone_intelligence_risk_idx on public.phone_intelligence(risk_score desc);

create or replace function public.set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

do $$ declare table_name text; begin
  foreach table_name in array array['dataset_sources','brands','dataset_items','review_queue','url_intelligence','phone_intelligence'] loop
    execute format('create trigger set_%I_updated_at before update on public.%I for each row execute function public.set_updated_at()',table_name,table_name);
  end loop;
end $$;

insert into public.dataset_sources(name,source_type,description,is_authoritative) values
  ('Guard user reports','user_report','Explicit community fraud reports submitted with contribution consent',false),
  ('Guard manual entry','manual','Records entered by authorised analysts',false),
  ('Guard authoritative patterns','authoritative_pattern','Curated patterns from verified advisories',true);

insert into public.fraud_categories(name,slug,description) values
 ('Phishing','phishing','Credential or payment capture through deceptive links or messages'),
 ('Mobile Money Fraud','mobile-money-fraud','Fraud involving mobile money accounts, transfers or reversals'),
 ('Impersonation','impersonation','Pretending to be a trusted person, brand or institution'),
 ('Fake Jobs','fake-jobs','Fraudulent employment or recruitment offers'),
 ('Investment Fraud','investment-fraud','False or misleading investment offers'),
 ('Prize or Promotion Scam','prize-promotion-scam','False winnings, rewards or promotional claims')
on conflict (slug) do nothing;

alter table public.dataset_sources enable row level security;
alter table public.brands enable row level security;
alter table public.dataset_items enable row level security;
alter table public.review_queue enable row level security;
alter table public.dataset_versions enable row level security;
alter table public.dataset_version_items enable row level security;
alter table public.model_versions enable row level security;
alter table public.model_predictions enable row level security;
alter table public.url_intelligence enable row level security;
alter table public.phone_intelligence enable row level security;

create policy "admins read sources" on public.dataset_sources for select using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
);
create policy "admins manage sources" on public.dataset_sources for all using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
) with check (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
);
create policy "admins manage dataset" on public.dataset_items for all using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
) with check (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
);
create policy "admins manage review queue" on public.review_queue for all using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
) with check (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst'))
);
create policy "admins read brands" on public.brands for select using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst','support_admin'))
);
create policy "admins read url intelligence" on public.url_intelligence for select using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst','support_admin'))
);
create policy "admins read phone intelligence" on public.phone_intelligence for select using (
  exists(select 1 from public.profiles p where p.id=auth.uid() and p.role in ('super_admin','fraud_analyst','support_admin'))
);

commit;
