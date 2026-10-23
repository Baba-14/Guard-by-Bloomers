begin;

create table public.organization_members (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  role text not null default 'viewer' check (role in ('owner','admin','developer','viewer')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_members_org_user_key unique (organization_id, user_id)
);

create index organization_members_organization_id_idx on public.organization_members(organization_id);
create index organization_members_user_id_idx on public.organization_members(user_id);

create trigger set_organization_members_updated_at before update on public.organization_members
for each row execute function public.set_updated_at();

commit;
