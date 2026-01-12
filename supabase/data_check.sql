-- Data checks for observations/timeseries coverage

-- 1) Yearly counts across all observations
select
  date_trunc('year', observed_at) as year_start,
  count(*) as row_count
from observations
group by 1
order by 1;

-- 2) Monthly counts for the last 18 months
select
  date_trunc('month', observed_at) as month_start,
  count(*) as row_count
from observations
where observed_at >= now() - interval '18 months'
group by 1
order by 1;

-- 3) 2025-only range across all observations
select
  count(*) as row_count,
  min(observed_at) as first_at,
  max(observed_at) as last_at
from observations
where observed_at >= '2025-01-01'::timestamptz
  and observed_at < '2026-01-01'::timestamptz;

-- 4) Latest observation timestamp overall
select
  max(observed_at) as latest_observed_at
from observations;

-- 5) Latest observation per series (top 25 most recent)
select
  timeseries_id,
  max(observed_at) as latest_observed_at
from observations
group by timeseries_id
order by latest_observed_at desc
limit 25;

-- 6) Check stations that have observations in 2025
select
  count(distinct ts.station_id) as stations_with_2025
from observations obs
join timeseries ts on ts.id = obs.timeseries_id
where obs.observed_at >= '2025-01-01'::timestamptz
  and obs.observed_at < '2026-01-01'::timestamptz;

-- 7) PM2.5 observations in 2025
select
  count(*) as row_count,
  min(obs.observed_at) as first_at,
  max(obs.observed_at) as last_at
from observations obs
join timeseries ts on ts.id = obs.timeseries_id
join phenomena phen on phen.id = ts.phenomenon_id
where obs.observed_at >= '2025-01-01'::timestamptz
  and obs.observed_at < '2026-01-01'::timestamptz
  and (
    lower(coalesce(phen.pollutant_label, '')) = 'pm2.5'
    or lower(coalesce(phen.notation, '')) = 'pm2.5'
    or lower(coalesce(phen.label, '')) like '%pm2.5%'
  );

-- 8) pcon boundaries presence (expects 2024 or 2023 version rows)
select
  pcon_version,
  count(*) as row_count
from pcon_boundaries
group by pcon_version
order by pcon_version;

-- 9) pcon_latest_pm25 coverage for a version
select
  pcon_version,
  count(*) as row_count,
  count(*) filter (where median_value is not null) as with_values
from pcon_latest_pm25
group by pcon_version
order by pcon_version;

-- 10) Quick sanity for timeseries last_value_at recency
select
  date_trunc('day', last_value_at) as day_start,
  count(*) as series_count
from timeseries
where last_value_at is not null
  and last_value_at >= now() - interval '30 days'
group by 1
order by 1;

-- 11) Find Bristol Temple Way station record(s)
select
  stn.id as station_id,
  stn.label as station_label,
  svc.label as service_label,
  stn.geometry
from stations stn
left join services svc on svc.id = stn.service_id
where stn.label ilike '%temple way%'
order by stn.label;

-- 12) Timeseries for Bristol Temple Way station(s)
select
  ts.id as timeseries_id,
  stn.label as station_label,
  phen.label as phenomenon_label,
  phen.notation as phenomenon_notation,
  ts.last_value_at,
  ts.last_value,
  ts.uom
from timeseries ts
join stations stn on stn.id = ts.station_id
left join phenomena phen on phen.id = ts.phenomenon_id
where stn.label ilike '%temple way%'
order by stn.label, phen.label nulls last;

-- 13) Observations coverage for Bristol Temple Way in 2025
select
  stn.label as station_label,
  count(*) as row_count,
  min(obs.observed_at) as first_at,
  max(obs.observed_at) as last_at
from observations obs
join timeseries ts on ts.id = obs.timeseries_id
join stations stn on stn.id = ts.station_id
where stn.label ilike '%temple way%'
  and obs.observed_at >= '2025-01-01'::timestamptz
  and obs.observed_at < '2026-01-01'::timestamptz
group by stn.label
order by stn.label;
