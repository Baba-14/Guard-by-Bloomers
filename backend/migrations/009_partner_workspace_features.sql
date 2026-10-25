begin;

alter table public.organizations
add column if not exists workspace_features jsonb not null default
  '["overview","reports","intelligence","customers","usage","keys","team"]'::jsonb;

update public.organizations
set workspace_features = '["overview","reports","intelligence","customers","usage","keys","team"]'::jsonb
where workspace_features is null;

commit;
