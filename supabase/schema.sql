create table if not exists public.card_rules (
  card_id text primary key,
  card_name text not null,
  bank text not null,
  network text not null,
  eligible_mccs text,
  earn_rate_mpd double precision not null,
  base_rate_mpd double precision not null,
  cap_sgd double precision,
  cap_period text not null,
  min_spend double precision default 0,
  requires_amaze boolean default false,
  amaze_fee_pct double precision default 0,
  eligible_merchants text,
  caveat text,
  last_verified text,
  source_url text,
  eligible_channels text,
  earn_block_sgd double precision default 1
);

create table if not exists public.merchant_mcc (
  merchant_name text not null,
  outlet text,
  channel text default 'any',
  mcc text not null,
  mcc_category text not null,
  confidence text not null,
  data_points integer default 0,
  last_verified text
);

create table if not exists public.rule_changes (
  change_id text primary key,
  changed_on date not null,
  effective_on date,
  entity_type text not null,
  entity_name text not null,
  change_type text not null,
  summary text not null
);

create index if not exists merchant_mcc_name_idx on public.merchant_mcc (merchant_name);
create index if not exists merchant_mcc_mcc_idx on public.merchant_mcc (mcc);
create index if not exists rule_changes_changed_on_idx on public.rule_changes (changed_on desc);

-- RLS with no policies: anon/authenticated keys get zero access; only the
-- service role key (used by the hosted loader) can read or write.
alter table public.card_rules enable row level security;
alter table public.merchant_mcc enable row level security;
alter table public.rule_changes enable row level security;

revoke all on table public.rule_changes from anon, authenticated;
grant select on table public.rule_changes to service_role;
