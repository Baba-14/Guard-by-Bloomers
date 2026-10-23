begin;

alter table public.partner_api_usage
add column if not exists customer_reference varchar(128);

create index if not exists partner_api_usage_customer_reference_idx
on public.partner_api_usage(organization_id, customer_reference);

create table if not exists public.partner_customers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  external_reference varchar(128) not null,
  display_name text,
  status text not null default 'active' check (status in ('active','suspended')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint partner_customers_org_reference_key unique (organization_id, external_reference)
);

create index if not exists partner_customers_organization_id_idx
on public.partner_customers(organization_id);

drop trigger if exists set_partner_customers_updated_at on public.partner_customers;
create trigger set_partner_customers_updated_at before update on public.partner_customers
for each row execute function public.set_updated_at();

insert into public.partner_customers (organization_id, external_reference)
select distinct organization_id, customer_reference
from public.partner_api_usage
where customer_reference is not null and customer_reference <> ''
on conflict (organization_id, external_reference) do nothing;

commit;
