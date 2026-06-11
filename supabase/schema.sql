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

create index if not exists merchant_mcc_name_idx on public.merchant_mcc (merchant_name);
create index if not exists merchant_mcc_mcc_idx on public.merchant_mcc (mcc);
