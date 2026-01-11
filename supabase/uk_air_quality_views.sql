-- Helper view + thresholds for Bristol AURN rendering

create table if not exists pollutant_thresholds (
  pollutant text,
  band int,
  label text,
  color text,
  lower_value numeric,
  upper_value numeric,
  uom text,
  primary key (pollutant, band)
);

insert into pollutant_thresholds (pollutant, band, label, color, lower_value, upper_value, uom)
values
  ('no2', 1, 'DAQI 1-3 (Low)', '#79BC6A', 0, 67, 'µg/m³'),
  ('no2', 2, 'DAQI 4-6 (Moderate)', '#BBCF4C', 68, 134, 'µg/m³'),
  ('no2', 3, 'DAQI 7-9 (High)', '#EEC20B', 135, 200, 'µg/m³'),
  ('no2', 4, 'DAQI 10 (Very High)', '#F29305', 201, null, 'µg/m³'),
  ('o3', 1, 'DAQI 1-3 (Low)', '#79BC6A', 0, 99, 'µg/m³'),
  ('o3', 2, 'DAQI 4-6 (Moderate)', '#BBCF4C', 100, 159, 'µg/m³'),
  ('o3', 3, 'DAQI 7-9 (High)', '#EEC20B', 160, 239, 'µg/m³'),
  ('o3', 4, 'DAQI 10 (Very High)', '#F29305', 240, null, 'µg/m³'),
  ('pm10', 1, 'DAQI 1-3 (Low)', '#79BC6A', 0, 16, 'µg/m³'),
  ('pm10', 2, 'DAQI 4-6 (Moderate)', '#BBCF4C', 17, 49, 'µg/m³'),
  ('pm10', 3, 'DAQI 7-9 (High)', '#EEC20B', 50, 75, 'µg/m³'),
  ('pm10', 4, 'DAQI 10 (Very High)', '#F29305', 76, null, 'µg/m³'),
  ('pm2.5', 1, 'DAQI 1-3 (Low)', '#79BC6A', 0, 11, 'µg/m³'),
  ('pm2.5', 2, 'DAQI 4-6 (Moderate)', '#BBCF4C', 12, 35, 'µg/m³'),
  ('pm2.5', 3, 'DAQI 7-9 (High)', '#EEC20B', 36, 53, 'µg/m³'),
  ('pm2.5', 4, 'DAQI 10 (Very High)', '#F29305', 54, null, 'µg/m³')
on conflict (pollutant, band) do update
set label = excluded.label,
    color = excluded.color,
    lower_value = excluded.lower_value,
    upper_value = excluded.upper_value,
    uom = excluded.uom;

create or replace view bristol_latest_pollutants as
with target_service as (
  select id
  from services
  where lower(label) like '%uk%' and lower(label) like '%air%'
  order by created_at asc
  limit 1
),
bristol_stations as (
  select stn.*
  from stations stn, target_service ts
  where stn.service_id = ts.id
    and stn.geometry && ST_MakeEnvelope(-2.75, 51.30, -2.45, 51.55, 4326)
),
latest as (
  select distinct on (obs.timeseries_id) obs.timeseries_id, obs.observed_at, obs.value, obs.status
  from observations obs
  order by obs.timeseries_id, obs.observed_at desc
)
select
  ts.id as timeseries_id,
  stn.id as station_id,
  stn.label as station_label,
  phen.id as phenomenon_id,
  phen.label as pollutant,
  ts.uom,
  latest.value as latest_value,
  latest.observed_at as observed_at,
  latest.status as status_flag,
  ts.last_value_at,
  ts.last_value,
  stn.geometry,
  coalesce(
    th.color,
    '#9ca3af'
  ) as color,
  ts.rendering_hints,
  ts.status_intervals,
  (ts.last_value_at is null or ts.last_value_at < now() - interval '3 hours') as is_stale
from timeseries ts
join bristol_stations stn
  on ts.station_id = stn.id
left join latest on latest.timeseries_id = ts.id
left join phenomena phen on phen.id = ts.phenomenon_id
left join pollutant_thresholds th
  on lower(phen.label) = th.pollutant
  and (
    (th.upper_value is null and latest.value is not null and latest.value >= th.lower_value) or
    (latest.value between th.lower_value and th.upper_value)
  );

-- Local authority latest PM2.5 (median + mean)
create or replace view la_latest_pm25 as
with pm25_candidates as (
  select
    ts.station_id,
    ts.last_value,
    ts.last_value_at,
    row_number() over (
      partition by ts.station_id
      order by ts.last_value_at desc nulls last
    ) as rn
  from timeseries ts
  join phenomena phen on phen.id = ts.phenomenon_id
  where ts.station_id is not null
    and ts.last_value is not null
    and ts.last_value_at is not null
    and (
      lower(coalesce(phen.pollutant_label, '')) = 'pm2.5'
      or lower(coalesce(phen.notation, '')) = 'pm2.5'
      or lower(coalesce(phen.label, '')) like '%pm2.5%'
    )
),
pm25_latest as (
  select
    stn.la_code,
    stn.la_version,
    pm.last_value,
    pm.last_value_at
  from pm25_candidates pm
  join stations stn on stn.id = pm.station_id
  where pm.rn = 1
    and stn.la_code is not null
),
pm25_agg as (
  select
    la_code,
    la_version,
    count(*)::int as station_count,
    percentile_cont(0.5) within group (order by last_value) as median_value,
    avg(last_value) as mean_value,
    max(last_value_at) as latest_value_at
  from pm25_latest
  group by la_code, la_version
)
select
  lb.la_code,
  lb.la_name,
  lb.la_version,
  pm25_agg.station_count,
  (pm25_agg.station_count = 1) as single_site,
  pm25_agg.median_value,
  pm25_agg.mean_value,
  pm25_agg.latest_value_at
from la_boundaries lb
left join pm25_agg
  on pm25_agg.la_code = lb.la_code
  and pm25_agg.la_version = lb.la_version;

-- Parliamentary constituency latest PM2.5 (median + mean)
create or replace view pcon_latest_pm25 as
with pm25_candidates as (
  select
    ts.station_id,
    ts.last_value,
    ts.last_value_at,
    row_number() over (
      partition by ts.station_id
      order by ts.last_value_at desc nulls last
    ) as rn
  from timeseries ts
  join phenomena phen on phen.id = ts.phenomenon_id
  where ts.station_id is not null
    and ts.last_value is not null
    and ts.last_value_at is not null
    and (
      lower(coalesce(phen.pollutant_label, '')) = 'pm2.5'
      or lower(coalesce(phen.notation, '')) = 'pm2.5'
      or lower(coalesce(phen.label, '')) like '%pm2.5%'
    )
),
pm25_latest as (
  select
    stn.pcon_code,
    stn.pcon_version,
    pm.last_value,
    pm.last_value_at
  from pm25_candidates pm
  join stations stn on stn.id = pm.station_id
  where pm.rn = 1
    and stn.pcon_code is not null
),
pm25_agg as (
  select
    pcon_code,
    pcon_version,
    count(*)::int as station_count,
    percentile_cont(0.5) within group (order by last_value) as median_value,
    avg(last_value) as mean_value,
    max(last_value_at) as latest_value_at
  from pm25_latest
  group by pcon_code, pcon_version
)
select
  pb.pcon_code,
  pb.pcon_name,
  pb.pcon_version,
  pm25_agg.station_count,
  (pm25_agg.station_count = 1) as single_site,
  pm25_agg.median_value,
  pm25_agg.mean_value,
  pm25_agg.latest_value_at
from pcon_boundaries pb
left join pm25_agg
  on pm25_agg.pcon_code = pb.pcon_code
  and pm25_agg.pcon_version = pb.pcon_version;

-- Enforce RLS on base tables for view readers.
alter view if exists bristol_latest_pollutants set (security_invoker = true);
alter view if exists la_latest_pm25 set (security_invoker = true);
alter view if exists pcon_latest_pm25 set (security_invoker = true);

revoke all on bristol_latest_pollutants from anon, authenticated;
revoke all on la_latest_pm25 from anon, authenticated;
revoke all on pcon_latest_pm25 from anon, authenticated;

grant select on bristol_latest_pollutants to authenticated, service_role;
grant select on la_latest_pm25 to authenticated, service_role;
grant select on pcon_latest_pm25 to authenticated, service_role;
