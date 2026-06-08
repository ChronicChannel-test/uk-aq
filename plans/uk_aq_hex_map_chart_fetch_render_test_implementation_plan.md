# UK AQ Hex Map Chart Fetch/Render TEST Implementation Plan

Status: planning only. Target TEST repos first. Do not update LIVE repos directly; use the existing sync-to-live process after TEST is accepted.

Related plan: `plans/uk_aq_hex_map_chart_fetch_render_plan_v4.md`

## Confirmed Decisions

1. Selected-hex chart session identity uses map scope plus stable area code. Do not use the visual hex cell key unless no stable area code exists.
2. Do not hard-code retention days. Implementation must read deployed config. Current TEST setting confirmed on 2026-06-08:
   - `ChronicChannel-test/uk-aq-ops`: `INGESTDB_RETENTION_DAYS=4`
   - `ChronicChannel-test/uk-aq-ingest`: `INGESTDB_RETENTION_DAYS=4`
3. `INGESTDB_RETENTION_DAYS` is the single source for both observation and AQI source splits.
4. Source splitting belongs behind the API/proxy boundary, not in `hex_map.html`. The frontend should request chart history by timeseries, pollutant, and range, then receive merged data plus source coverage metadata.
5. Historical observation ranges must not fall back to ingestdb. Only the retention range and one-day overlap may use ingestdb.
6. Initial AQI chunk sizes:
   - 12h/24h: one chunk
   - 7d: one-day chunks
   - 31d: three-day chunks
   - 90d: seven-day chunks
7. Initial observation chunk sizes:
   - 12h/24h: one chunk
   - 7d: one-day chunks
   - 31d: two-day chunks
   - 90d: five-to-seven-day chunks
8. Initial concurrency:
   - AQI active source: 4
   - Primary observation line: 3, starting only after all active-source AQI fetches for the requested range have completed
   - Additional selected timeseries observations: 2 per timeseries, with a global chart cap
   - Background AQI prefetch: 1 or 2
   - Global chart fetch cap: 6
9. Empty responses can mark ranges as covered only when the response is valid and explicitly complete. Use range states such as `covered_empty`, `covered_with_data`, `failed`, `partial`, `malformed`, and `unknown`.
10. Debug output is console-only for now, behind URL flags such as `?debug_aqi=1` and `?debug_chart=1`.
11. AQI cache keys should include `timeseries_id`, `station_id`, `connector_id`, and `pollutant_code`.
12. Observation cache keys should include `timeseries_id`, `pollutant_code`, and `connector_id` if available.
13. Store source metadata per interval so gaps and mixed-source periods are explainable.

## Split Config Status

TEST previously had two split controls:

- Ops/AQI: `INGESTDB_RETENTION_DAYS=4`
- Ingest timeseries edge function: a separate 120-hour observation split

Phase 4 removes the independent observation split by making the observation API read `INGESTDB_RETENTION_DAYS`. Any hours value exposed in `uk_aq_timeseries` metadata is derived from `INGESTDB_RETENTION_DAYS * 24` for compatibility only.

## Recommended Implementation Path For TEST

### Phase 1: Debug Instrumentation

Files/functions:

- `hex_map.html`: debug flag helpers around `isAqiHistoryDebugEnabled`
- `hex_map.html`: AQI fetch/render metadata logging
- `hex_map.html`: observation fetch/render metadata logging
- `workers/uk_aq_aqi_history_r2_api_worker/worker.mjs`: AQI response metadata
- `supabase/functions/uk_aq_timeseries/index.ts`: timeseries response payload/source metadata

Acceptance checks:

- `?debug_aqi=1` logs selected AQI source, `station_id`, `timeseries_id`, `connector_id`, pollutant, chart range, requested AQI URLs, response status, response metadata, raw row count, parsed point count, parsed gap ranges, cache state, and rendered segment counts.
- `?debug_chart=1` logs selected chart identity, range resolution, observation request URLs, response status, response metadata, raw row count, parsed point count, source coverage, cache state, and rendered line/gap counts.
- Debug logging does not require cache-buster params for normal use.
- Debug logging is console-only and does not change production rendering.

Manual browser tests:

- Open 24h, 7d, 31d, and 90d charts.
- Switch AQI source.
- Select a second timeseries.
- Confirm debug logs show enough information to explain missing AQI bands or line gaps.

Local/DuckDB checks:

- Compare AQI R2 rows for a known timeseries/day against AQI worker response counts and frontend parsed counts.
- Compare observation R2 rows for a known timeseries/day against timeseries response counts and frontend parsed counts.

Impact:

- Supabase billable egress: negligible from console-only frontend logging; small response egress increase if API metadata payloads expand.
- R2/Cloudflare cost: unchanged except possible diagnostic test traffic.
- Database size: unchanged.

### Phase 2: Frontend Cache Hardening

Files/functions:

- `hex_map.html`: `seriesDataCache`
- `hex_map.html`: `aqiBandCache`
- `hex_map.html`: covered-range helpers
- `hex_map.html`: fetch queues and request scheduling

Acceptance checks:

- Cache entries distinguish `covered_empty`, `covered_with_data`, `failed`, `partial`, `malformed`, and `unknown`.
- Failed, malformed, partial, or misparsed responses never mark a range covered.
- Empty responses mark covered only when the API explicitly reports the requested range as valid and complete.
- Concurrent identical range requests deduplicate through in-flight request tracking.
- Expanding 24h to 7d/31d/90d fetches only missing intervals.
- Contracting range refetches nothing.
- Re-expanding uses cached covered intervals.
- Source metadata is stored per interval.
- AQI cache keys include `timeseries_id`, `station_id`, `connector_id`, and `pollutant_code`.
- Observation cache keys include `timeseries_id`, `pollutant_code`, and `connector_id` if available.

Manual browser tests:

- Expand 24h to 7d to 90d.
- Contract back to 24h.
- Re-expand to confirm cached data is reused.
- Simulate a failed AQI URL if practical and confirm failed ranges do not poison covered ranges.

Local tests:

- Add or update JavaScript tests if the existing harness can exercise cache helpers.
- Test missing-range calculation, failed-range preservation, and in-flight request deduplication.

Impact:

- Supabase billable egress: should decrease for repeated expand/contract interactions because duplicate DB/API reads are avoided.
- R2/Cloudflare cost: should decrease for repeated range changes due to fewer duplicate R2/API requests.
- Database size: unchanged.

### Phase 3: Chart Session/Range Confirmation

Files/functions:

- `hex_map.html`: chart mode `enter`
- `hex_map.html`: chart mode `exit`
- `hex_map.html`: chart range change handler
- `hex_map.html`: selected hex identity resolution

Acceptance checks:

- Chart range defaults to 24h when chart mode opens for a newly selected hex.
- If the user changes range, exits chart mode, and returns without selecting a different hex, the last range persists.
- Selecting a different hex resets the range to 24h.
- Returning to the original hex after another hex also resets to 24h.
- Session identity is map scope plus stable area code, falling back to visual hex cell key only when no stable area code exists.

Manual browser tests:

- Select hex A, open chart, set 7d, exit, re-enter A: range remains 7d.
- Select hex B: range resets to 24h.
- Return to hex A after B: range resets to 24h.
- Repeat across map scopes if more than one map scope can produce the same area code.

Impact:

- Supabase billable egress: neutral to slight decrease because accidental stale-session refetches should reduce.
- R2/Cloudflare cost: neutral to slight decrease for the same reason.
- Database size: unchanged.

### Phase 4: Observation Source Planning

Files/functions:

- `supabase/functions/uk_aq_timeseries/index.ts`: observation source split and merge
- `workers/uk_aq_observs_history_r2_api_worker/worker.mjs`: R2 observation history response/coverage metadata
- `workers/uk_aq_cache_proxy/src/index.ts`: proxy contract if source splitting is moved into the proxy boundary
- `workers/uk_aq_cache_proxy/src/timeseries_v2_stitch.mjs`: merge/source coverage helpers if used

Acceptance checks:

- Retention range queries ingestdb only.
- One-day overlap prefers R2 and fills missing hours from ingestdb.
- Historical range queries R2 only.
- Historical observation ranges do not fall back to ingestdb.
- ObsAQIDB is never called for observation line data.
- R2 wins duplicate hours when both R2 and ingestdb return the same observation hour.
- Response includes source coverage metadata by interval.
- R2 observation worker responses expose explicit completeness state, not just `ok: true`, including whether missing day manifests, missing connector manifests, missing parquet files, or skipped index days make the response partial.
- `uk_aq_timeseries` maps incomplete R2 observation coverage to `response_complete=false` / `has_gap=true` and does not mark those chunks complete.
- Frontend observation cache records incomplete R2-backed chunks as `partial`, `failed`, `malformed`, or `unknown`, not `covered_empty`.
- Source split reads deployed `INGESTDB_RETENTION_DAYS`, currently 4 in TEST, rather than hard-coded days or independent timeseries hours.

Manual browser tests:

- Open 24h, 7d, 31d, and 90d charts with `?debug_chart=1`.
- Confirm debug/source metadata shows ingestdb only inside retention, mixed R2/ingestdb only in overlap, and R2 only in historical ranges.

Local/DuckDB checks:

- Inspect R2 observation availability by day/hour.
- Compare missing-overlap fills against ingestdb rows.
- Verify historical windows without R2 rows return complete empty or partial metadata, not ingestdb fallback.
- For a known timeseries with R2 data, compare each 7-day/90-day chart chunk against R2 rows and confirm `r2_row_count`, `row_count`, and frontend `parsed_point_count` agree.
- Simulate or identify a missing manifest/index day and confirm the response is partial, not `covered_empty`.

Impact:

- Supabase billable egress: expected decrease for historical observation ranges because historical line data should come from R2 rather than Supabase.
- R2/Cloudflare cost: expected increase for historical observation chart requests; keep stable URLs to maximize Cloudflare cache hits and limit R2 Class B reads.
- Database size: unchanged.

### Phase 5: AQI Source Planning Cleanup

Files/functions:

- `workers/uk_aq_aqi_history_r2_api_worker/worker.mjs`: AQI split, merge, and response coverage metadata
- `workers/uk_aq_cache_proxy/src/index.ts`: proxy routing/contract if AQI planning is centralized there
- `hex_map.html`: consume AQI metadata for debug/cache state, not for source planning

Acceptance checks:

- No R2 AQI fetch inside retention range.
- One-day overlap prefers R2 and fills missing hours from ObsAQIDB.
- ObsAQIDB reads only missing overlap hours if practical.
- Historical AQI is R2 only.
- Ingestdb is never used for AQI bands.
- R2 wins duplicate hours.
- Response exposes `INGESTDB_RETENTION_DAYS` used for the split.
- Response exposes source coverage metadata by interval.

Implementation notes:

- Phase 5 is implemented in the TEST AQI history R2 API worker.
- AQI source splitting uses the same rolling `INGESTDB_RETENTION_DAYS` boundary as observation history.
- The worker now exposes `overlap_start_utc`, `retention_start_utc`, `coverage.source_coverage`, `coverage_state`, `has_gap`, and `partial_reasons`.
- The cache proxy and `hex_map.html` remain consumers of AQI metadata; source planning stays behind the API/proxy boundary.

Manual browser tests:

- Confirm AQI bands render for recent 24h, overlap boundary, and 31d history.
- Use `?debug_aqi=1` to confirm retention, overlap, and historical source choices.

Local/DuckDB checks:

- Compare R2 AQI history and ObsAQIDB hourly AQI around the cutover.
- Confirm overlap missing-hour repair matches expected source priority.

Impact:

- Supabase billable egress: expected decrease for historical AQI ranges because historical bands should come from R2 rather than Supabase.
- R2/Cloudflare cost: expected increase for historical AQI requests; stable URLs and cache hits are important.
- Database size: unchanged.

### Phase 6: AQI-First Fetching And Background Prefetch Timing

Files/functions:

- `hex_map.html`: `loadChartData`
- `hex_map.html`: AQI active-source fetch queue
- `hex_map.html`: observation fetch queues
- `hex_map.html`: `prefetchAqiBandsForEntries`
- `hex_map.html`: AQI band rendering/sync

Acceptance checks:

- On fresh chart load, frontend establishes pollutant, selected hex identity, chart range, first selected timeseries, and AQI source timeseries before fetching.
- AQI source chunks start first.
- No observation history fetches start while there are outstanding active-source AQI history fetches for the requested range.
- Primary observation history fetches start only after all active-source AQI history fetches for the requested range have completed.
- AQI chunks prioritize newest-to-oldest rendering, visually right to left.
- Added timeseries observation lines render promptly when observation data arrives.
- Selecting an additional timeseries does not change or repaint AQI bands.
- Background AQI prefetch for non-source selected timeseries runs at concurrency 1 or 2.
- Background AQI prefetch does not repaint AQI bands.
- Switching AQI source uses prefetched AQI bands immediately when available.
- Global chart fetch cap is 6.

Implementation notes:

- Phase 6 is implemented in TEST `hex_map.html`.
- Active-source AQI chunks run before observation chunks and use concurrency 4.
- Observation chunks do not start until active-source AQI chunks have completed; observation fetches use a global cap of 6, primary-timeseries cap 3, and additional-timeseries cap 2.
- Observation line chunks commit in completion order so added timeseries render as soon as their data arrives.
- Background AQI prefetch for non-source selected timeseries runs at concurrency 2 and only writes AQI cache; it does not repaint current AQI bands.

Manual browser tests:

- Throttle network and confirm no observation history requests start until all active-source AQI history requests have completed.
- Confirm AQI bands render before observation lines.
- Add/remove selected timeseries.
- Switch AQI source after background prefetch.
- Confirm non-source AQI prefetch does not repaint current bands.

Impact:

- Supabase billable egress: neutral to slight decrease when prefetched/cached data avoids duplicate source requests; possible short-term increase when prefetching AQI for selected non-source timeseries.
- R2/Cloudflare cost: possible increase from background AQI prefetch, mitigated by concurrency limits, selected-timeseries-only scope, stable URLs, and cache hits.
- Database size: unchanged.

## Recommended Strategy

Use the staged implementation above. It is safer than a frontend-only change because source selection is an API concern, and safer than a backend-only change because the current chart still needs cache hardening, session identity rules, and AQI-first scheduling.

Less complete alternatives:

- Frontend-only alignment: faster, but risks putting retention/source split rules into `hex_map.html`, which conflicts with the API-boundary decision and is harder to keep consistent with AQI.
- API/proxy-only cleanup: improves source correctness, but leaves chart cache poisoning, range persistence, and AQI prefetch timing unresolved.
- Full staged implementation: more work, but best preserves expand/contract behavior while making source selection observable and testable.

## Global Regression Checks

- No LIVE repo edits.
- No archive file edits.
- No client-side production AQI band calculation from observations.
- No ObsAQIDB usage for observation line data.
- No R2 requests inside the retention range for observations or AQI.
- No website polling reduction below one minute.
- No aggregation/downsampling of raw history data.
- Range expansion/contraction behavior remains intact.
