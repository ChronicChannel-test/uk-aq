# UK-AQ Supabase Schema Overview

This document summarizes the schema defined in `supabase/uk_air_quality_schema.sql` for ingesting UK-AIR SOS / 52°North timeseries data and PM2.5 target tracking.

## Extensions
- `postgis` for spatial columns (geography Point).
- `pgcrypto` for UUID generation (gen_random_uuid).

## Core reference tables
- External identifiers that arrive as text (even if numeric) are stored as `*_ref`; all `*_id` columns are internal bigint keys.
- `services`: SOS instances with bigint `id` (internal) and `service_ref` (external), plus URL and polling fields (`poll_enabled`, `poll_interval_minutes`, `poll_window_hours`, `poll_timeseries_batch_size`, `stations_bbox_supported`, `timeseries_station_filter_supported`, `last_polled_at`).
- `categories`: high-level grouping, per service.
- `phenomena`: what is measured (pollutant/parameter), per service; includes optional `eionet_uri` + `notation`.
- `offerings`: logical groupings, per service.
- `features`: features of interest with geometry (Point, 4326), per service.
- `procedures`: sensors/methods; optional raw_formats list, per service.
- `stations`: monitoring sites; bigint `id` (internal) with `station_ref` (external), unique `(service_id, station_ref)`, plus lifecycle fields `first_seen_at`, `last_seen_at`, `removed_at`. Also stores `la_code`/`la_version` and `pcon_code`/`pcon_version` for geography lookups.

## Geography mapping tables
- `la_boundaries`: Local Authority polygons (MultiPolygon, 4326) with `la_code` + `la_version` for assigning stations to LAs.
- `pcon_boundaries`: Parliamentary Constituency polygons (MultiPolygon, 4326) with `pcon_code` + `pcon_version` for assigning stations to constituencies.
- `uk_aq_refresh_station_la_codes(target_version)`: updates `stations.la_code` + `stations.la_version` using `la_boundaries`.
- `uk_aq_refresh_station_pcon_codes(target_version)`: updates `stations.pcon_code` + `stations.pcon_version` using `pcon_boundaries`.

## Timeseries and metadata
- `timeseries`: SOS timeseries metadata; bigint `id` (internal) with `timeseries_ref` (external) and `station_id` bigint FK.
- `reference_values`: optional reference lines attached to a timeseries (name, color, value).

## Observations
- `observations`: raw time-value pairs for each timeseries (observed_at timestamptz, value, status flag). Primary key is `(timeseries_id, observed_at)`.

## PM2.5 target tracking (optional)
- `pm25_population_exposure`: yearly Population Exposure Indicator (PEI) series with deltas and % change vs 2018 baseline.
- `pm25_amct_sites`: annual mean concentration per site/year to track AMCT and interim exceedances.

## Constituency reference tables
- `pcon_current`: current constituency electorate data (`gss_code`, `name`, `electorate`, `region`, `country`).
- `pcon_legacy`: legacy constituency electorate data for historical backfill (same columns as `pcon_current`).
- `gss_codes`: canonical registry of GSS codes across geographies (`gss_code`, `name`, `geography_type`, `valid_from`, `valid_to`).

## Guideline limits
- `uk_aq_guidelines`: pollutant guideline limits (WHO/UK/EU, etc.) with `pollutant`, `averaging_period_label`, `averaging_period_interval`, `level_label`, `limit_value`, `uom`, and optional `source`/`notes`/validity dates.

## Views
- `pcon_latest_pm25` (in `supabase/uk_air_quality_views.sql`): constituency-level PM2.5 summaries keyed by `pcon_code` + `pcon_version` with median/mean, station_count, and last update timestamp.

## RLS (Row Level Security)
- RLS enabled on all domain tables (not on system tables like spatial_ref_sys).
- Policies (idempotent via DO block):
  - `select`: allowed for roles `authenticated` and `service_role`.
  - `all` (insert/update/delete): allowed for `service_role` only.
- Adjust policies if you need anon read or user-owned row scoping.

## Notes on multi-pollutant support
- Schema is pollutant-agnostic: add new phenomena, stations, timeseries, and observations for NO2, O3, PM10, etc. No structural changes needed.

## Minimal ingestion flow
1) Discover metadata from the SOS REST API: services, stations, timeseries (use `expanded=true` for richer fields).
2) Upsert metadata into `services`, `stations`, `timeseries`, and related reference tables.
3) Fetch data via `/timeseries/{id}/getData` (format=tvp) and insert into `observations` (convert epoch ms to timestamptz).
4) Store optional `referenceValues`, `status_intervals`, `rendering_hints`, and `extras` when present.
