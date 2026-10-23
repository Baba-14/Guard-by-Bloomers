begin;

create table public.telegram_updates (
  update_id bigint primary key,
  chat_id bigint not null,
  message_id bigint,
  check_id uuid references public.checks(id) on delete set null,
  processing_status text not null default 'processing',
  alert_delivery_status text not null default 'not_required',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index telegram_updates_chat_id_idx on public.telegram_updates(chat_id);

create trigger set_telegram_updates_updated_at before update on public.telegram_updates
for each row execute function public.set_updated_at();

commit;
