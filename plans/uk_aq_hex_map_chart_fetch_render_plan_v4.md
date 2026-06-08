# UK AQ hex map chart fetch and render plan v4

## Purpose

This plan defines how the `hex_map.html` chart mode should fetch, cache, and render:

- AQI coloured bands
- selected sensor line chart data
- range expansion and contraction
- additional selected sensors
- R2 history data
- ingestdb tail data during the ingest retention period

The aim is to make the chart behaviour predictable before fixing the remaining AQI band gap issue.

## Repositories

### Live

- Website: `https://github.com/Chronic-Illness-Channel/uk-aq`
- Website file of interest: `hex_map.html`
- Ops: `https://github.com/Chronic-Illness-Channel/uk-aq-ops`
- Ingest: `https://github.com/Chronic-Illness-Channel/uk-aq-ingest`

### Test

- Website: `https://github.com/ChronicChannel-test/uk-aq`
- Website file of interest: `hex_map.html`
- Ops: `https://github.com/ChronicChannel-test/uk-aq-ops`
- Ingest: `https://github.com/ChronicChannel-test/uk-aq-ingest`

## Current assumptions to confirm

The implementation work should confirm these before making changes:

1. `hex_map.html` owns the chart state, selected sensors, AQI source sensor, chart range selection, and rendering.
2. The ingest repo contains the Supabase timeseries edge function used by chart observation history.
3. The ops repo contains the cache proxy and the R2 AQI history worker.
4. The AQI levels used for coloured bands should prefer R2 AQI history, not client-side recalculation.
5. There will never be R2 history for observations or AQI levels inside the configured `ingest_retention_days` range.
6. For the extra one-day overlap beyond the retention range, R2 history may or may not exist.
7. For AQI bands inside the retention range, use obsaqidb directly and do not try R2.
8. For AQI bands in the one-day overlap just beyond the retention range, prefer R2 if present, then fall back to obsaqidb if missing.
9. Observation history older than the ingest retention period should come from R2 history.
10. Fresh observation history inside the ingest retention period exists in ingestdb, not R2.
11. ingestdb should be used for observation line data inside the retention range.
12. obsaqidb should not be used for observation line data at this stage.

## Definitions

### Chart range

The user-selected range in chart mode, for example:

- Last 12 hours
- Last 24 hours
- Last 7 days
- Last 31 days
- Last 90 days

### Chart range default and persistence

The chart range should default to **Last 24 hours**.

This default should apply whenever chart mode is opened for a newly selected hex.

Persistence rule:

- If the user opens chart mode for a hex, changes the chart range, leaves chart mode, and then returns to chart mode **without selecting a different hex**, the last selected chart range should persist.
- If the user selects a different hex, the chart range should reset to **Last 24 hours** for that new hex.
- If the user later returns to the original hex after selecting a different hex, that should also count as a new chart session for that hex, so the chart range should again default to **Last 24 hours**.

In other words:

- chart range persists only while the selected hex has not changed
- selecting any different hex clears the previous chart-range session state
- default chart range is always 24 hours for a new selected-hex chart session

Implementation intent:

- keep a current selected hex identity, for example `currentChartHexKey`
- keep a chart range value for the active chart session
- when entering chart mode, compare the target hex key with the previous chart hex key
- if the target hex key is the same, reuse the last selected range
- if the target hex key is different, reset the range to `24h`
- update the toolbar/select UI to show `24h` after a hex change
- ensure reset to 24h triggers the correct fetch/render plan for 24h, not the previous range

Do not persist chart range globally across different hexes.

Do not persist chart range in local storage at this stage unless explicitly decided later.

### Window

The map averaging window, for example 1 hour, 6 hours, or 24 hours.

This should continue to affect map values, sensor list ordering, and current readings, but it should not break chart range behaviour.

### Primary chart sensor

The first selected chart sensor. This sensor is the default AQI band source.

### AQI source sensor

The selected sensor whose AQI history is used for the DAQI and EAQI coloured bands.

Default behaviour:

- the AQI source sensor is the first selected chart sensor
- changing the AQI source sensor should switch the AQI bands to the selected sensor
- additional selected sensors should not automatically change the AQI source sensor

### Retention range and one-day overlap

The recent retention range is the period where history has not yet been written to R2.

Current value:

- `ingest_retention_days = 4`

This value may change, so the chart logic should not hard-code 4 days. It should read the configured value or receive it from the API/config where possible.

Define:

- `retention_start = now - ingest_retention_days`
- `overlap_start = now - (ingest_retention_days + 1 day)`
- `now = current UTC time`

This creates two recent sub-ranges:

1. **Retention range**
   - `retention_start` to `now`
   - there will never be R2 history for observations or AQI levels in this range
   - do not fetch R2 for this range

2. **One-day overlap**
   - `overlap_start` to `retention_start`
   - R2 history may or may not be present
   - prefer R2 where available
   - fall back to live database sources for missing hours only

For observation line data:

- retention range source: ingestdb only
- one-day overlap source: R2 preferred, ingestdb fallback for missing hours
- older than one-day overlap: R2 only

For AQI band data:

- retention range source: obsaqidb only
- one-day overlap source: R2 preferred, obsaqidb fallback for missing hours
- older than one-day overlap: R2 only

## Desired high-level behaviour

### Fresh chart load

When chart mode opens for a selected area and selected sensor:

1. Establish selected pollutant.
2. Establish whether the selected hex is the same as the previous chart-session hex.
3. If it is the same hex, reuse the last selected chart range.
4. If it is a different hex, reset chart range to `24h`.
5. Establish the primary chart sensor.
6. Set the AQI source sensor to the primary chart sensor, unless already explicitly selected for the current chart session.
7. Fetch AQI history for the AQI source sensor first.
8. Start all required AQI history chunk requests in parallel.
9. Render AQI bands as soon as AQI chunks arrive.
10. Render AQI bands from newest to oldest, visually right to left.
11. Then fetch observation history for the line chart.
12. Render observation history as chunks arrive.
13. Render observation line chunks from newest to oldest, visually right to left.
14. Preserve the current smooth expand/contract behaviour when the chart range changes.

### Chart range changes

The current behaviour for expanding and contracting ranges is working well and must not be broken.

Required behaviour:

- Contracting a range should not refetch data that is already in memory.
- Expanding a range should fetch only the missing older or newer interval.
- Existing visible line and AQI band data should remain visible while missing intervals load.
- New chunks should be merged into the existing cache.
- The x-domain should update cleanly without wiping useful already-fetched data.
- The right-to-left loading preference should apply only to missing intervals, not to already-cached intervals.

### Sensor selection changes

When the user selects additional sensor(s):

1. The line chart for the newly selected sensor should render as soon as possible.
2. Do not switch or redraw the AQI bands just because another sensor was selected.
3. Keep the AQI bands tied to the current AQI source sensor.
4. Fetch observation history for the added sensor.
5. Render the added sensor line from newest to oldest as chunks arrive.
6. After observation history for the added sensor is requested or available, prefetch AQI history for that sensor in the background.
7. The reason for background AQI prefetch is so that if the user later chooses that sensor as the AQI source, its bands can display immediately.

When a sensor is deselected:

- Remove its line from the chart.
- Do not clear its cached observation history unless memory pressure makes that necessary.
- Do not clear its prefetched AQI history unless memory pressure makes that necessary.
- If the deselected sensor was the AQI source, move the AQI source back to the first selected sensor and render from cache if available.

## Fetch priority model

### Priority 1: AQI bands for the current AQI source sensor

AQI bands should be the first visible chart layer to complete.

For a fresh chart:

- split the selected chart range into AQI request chunks
- enqueue all AQI chunks for the AQI source sensor
- run AQI chunk fetches in parallel, with a sensible concurrency limit
- prefer rendering chunks from newest to oldest
- merge each successful chunk into the AQI cache
- update the DAQI and EAQI bands after each chunk, or after each batch if that is smoother

AQI fetches should not block the UI completely. The chart frame can be created immediately, but the AQI bands are the first data layer to populate.

### Priority 2: Observation line for the primary sensor

After AQI band fetches have started, fetch the observation history for the primary chart sensor.

The line should render incrementally from newest to oldest.

### Priority 3: Observation lines for additional selected sensors

For every additional selected sensor:

- fetch missing observation history
- render as chunks arrive
- do not alter the AQI bands
- then prefetch AQI history for that sensor in the background

### Priority 4: AQI prefetch for non-source selected sensors

AQI prefetch should run after observation fetches for those sensors have been started.

The background AQI prefetch should:

- use the same selected pollutant
- use the same selected chart range
- use the same chunking and cache key strategy as active AQI bands
- not redraw the bands unless that sensor becomes the AQI source
- not interrupt active line rendering

## Recent data source model

Recent chart data is split into three time zones:

1. **Retention range**
   - `now - ingest_retention_days` to `now`
   - R2 history will not exist here
   - never fetch R2 for observations or AQI in this range

2. **One-day overlap**
   - `now - (ingest_retention_days + 1 day)` to `now - ingest_retention_days`
   - R2 history may or may not exist here
   - prefer R2 where available
   - fill missing hours from live database sources

3. **Historical range**
   - older than `now - (ingest_retention_days + 1 day)`
   - R2 should be the source
   - do not query live database sources

### Observation source plan

For every observation line request:

1. Split the requested chart range into historical, one-day overlap, and retention sub-ranges.
2. Fetch the historical range from R2 only.
3. Fetch the one-day overlap from R2 first.
4. Identify missing observation hours in the one-day overlap.
5. Fetch only those missing one-day-overlap observation hours from ingestdb.
6. Fetch the retention range from ingestdb directly.
7. Do not attempt R2 for the retention range.
8. Merge R2 and ingestdb observation points.
9. If the same observation hour exists in both R2 and ingestdb, prefer R2.
10. Record source metadata per interval for debugging.

### AQI band source plan

For every AQI band request:

1. Split the requested chart range into historical, one-day overlap, and retention sub-ranges.
2. Fetch the historical AQI range from R2 only.
3. Fetch the one-day overlap AQI range from R2 first.
4. Identify missing AQI hours in the one-day overlap.
5. Fetch only those missing one-day-overlap AQI hours from obsaqidb.
6. Fetch the retention range from obsaqidb directly.
7. Do not attempt R2 for AQI in the retention range.
8. Merge R2 and obsaqidb AQI points.
9. If the same AQI hour exists in both R2 and obsaqidb, prefer R2.
10. Render the merged DAQI and EAQI bands.
11. Record source metadata per interval for debugging.

The frontend or API should make the resulting source coverage debuggable, so it is clear whether a visible AQI band segment came from R2, ingestdb, or obsaqidb.

## Data source rules

### AQI bands

AQI bands should prefer R2 AQI history wherever it exists.

Use:

- R2 `aqilevels`
- AQI history endpoint
- `timeseries_id`
- `station_id` if required by the endpoint
- `pollutant_code`
- hourly timestamps

For the retention range, AQI levels will not be in R2. Therefore, for AQI bands only, obsaqidb is required as the source inside the retention range.

AQI band source rules:

- for the range older than the one-day overlap, use R2 only
- for the one-day overlap just beyond the retention range, prefer R2 where available
- for missing AQI hours inside the one-day overlap, fill from obsaqidb
- for the retention range itself, use obsaqidb directly and do not try R2
- the retention range is `ingest_retention_days`
- the overlap range is one extra day beyond the retention range
- do not use ingestdb for AQI bands
- do not calculate production AQI bands client-side from observation values

Client-side AQI calculation may be useful later as a debug-only fallback, but it should not be the normal display path.

### Observation history

Observation line chart data should prefer R2 history whenever it exists.

For the part of the requested range older than the retention range:

- use R2 only
- do not query ingestdb
- do not query obsaqidb

For the retention range:

- do not query R2
- use ingestdb for observation line data
- do not use obsaqidb for observation line data

For the one-day overlap beyond the retention range:

- prefer R2 if it has been materialised
- if R2 has missing hours in the one-day overlap, fill those missing hours from ingestdb
- do not use obsaqidb for observation line data

This means the logic should not blindly query ingestdb for the whole chart range.

It should only use ingestdb for:

- `now - (ingest_retention_days + 1 day)` to `now`
- and only for missing intervals that are not available from R2

### obsaqidb

Use obsaqidb for AQI band data inside the retention range and as fallback for missing AQI hours in the one-day overlap.

Do not use obsaqidb for observation line chart data in this plan.

obsaqidb source rules:

- allowed for AQI bands
- used directly for AQI bands inside the retention range
- used as fallback for missing AQI hours in the one-day overlap
- not queried for AQI older than the one-day overlap
- not used for observation lines
- not used as the preferred source when R2 has the same AQI hour

This keeps obsaqidb reads bounded and avoids using it for older chart ranges where R2 should be authoritative.

## Chunking and ordering

### Right-to-left rendering

The user sees time moving left to right, with newest data on the right.

For perceived responsiveness, new data should appear from the right first.

Fetch/render order should therefore prefer:

1. newest missing chunk
2. next newest missing chunk
3. continue backwards until the oldest missing chunk is complete

For AQI bands, the browser should be able to show the newest DAQI/EAQI band segments while older chunks are still loading.

For observation lines, the newest line segment should appear while older chunks are still loading.

### Parallel AQI fetches

For a fresh chart, the AQI source sensor’s AQI chunks should be started in parallel.

Recommended approach:

- create a chunk work queue sorted newest to oldest
- start up to `AQI_HISTORY_CONCURRENCY` requests
- as each request completes, merge it and render
- continue until queue is empty

The concurrency value should be conservative to avoid too many R2/API requests at once.

Suggested initial value:

- 3 or 4 concurrent AQI chunks

### Observation fetches

Observation fetches may also use chunking, but they should be balanced so that AQI bands still get priority on fresh chart load.

Recommended approach:

- primary sensor observation chunks start after AQI fetch queue has started
- additional sensor observation chunks start after the primary sensor is underway
- each sensor’s newest chunks should be prioritised first

## Cache model

### Cache keys

AQI cache key should include:

- `timeseries_id`
- `station_id` if needed
- `pollutant_code`
- source identity if needed to avoid collisions

Observation cache key should include:

- `timeseries_id`
- `pollutant_code`
- source identity if needed to avoid collisions

Cache records should store:

- points
- covered ranges
- failed ranges, separately from covered ranges
- in-flight requests
- source used for each interval if relevant, for example R2 or ingestdb
- last updated timestamp

### Important cache rule

Do not mark a range as covered if:

- the request failed
- the response was malformed
- the response was parsed but produced no rows unexpectedly
- the response field names did not match
- the endpoint returned an error status
- the endpoint returned partial data without clear metadata

A failed range can be recorded as failed, but it must not poison the covered range cache.

### Merging points

When chunks arrive:

- normalise timestamps to UTC hourly timestamps
- deduplicate by `period_start_utc`
- prefer R2 values over ingestdb values if both exist for the same timestamp
- sort points by timestamp
- do not create duplicate chart points
- do not create duplicate AQI band segments

## Rendering model

### Chart frame

The chart frame should be created once and reused.

It should include:

- x-axis
- y-axis
- AQI band container
- line container
- symbol/dot container
- hover/tooltip layer

Avoid clearing and rebuilding the entire SVG unless absolutely necessary.

### AQI bands

DAQI and EAQI rows should render independently.

Render rules:

- DAQI row uses DAQI index levels
- EAQI row uses EAQI index levels
- missing DAQI should create a DAQI gap only
- missing EAQI should create an EAQI gap only
- a missing hour should be visible as a real gap, not hidden by stretching neighbouring segments
- adjacent same-level hours can be merged into wider rectangles
- non-adjacent same-level hours must not be merged across gaps
- segments should be clipped to the current x-domain
- timestamps should be treated as hourly start times

If the API returns point rows, the frontend can convert them into hourly rectangles.

If the API returns run-length segments, the frontend can render those directly, but it must still respect gaps.

### Line chart

Line chart rules:

- each selected sensor gets a line
- line data renders from newest to oldest as chunks arrive
- gaps in observation data should be shown as gaps in the line, not connected across missing periods
- already-rendered points should remain visible while older chunks load
- adding a sensor should not clear existing lines
- removing a sensor should remove only that sensor’s line
- changing the chart range should preserve current expand/contract behaviour

## AQI band issue investigation hooks

The current AQI bands can show gaps even where R2 data may exist.

Before changing the main logic, add debug visibility so the source of gaps can be proved.

Debug mode should be opt-in, for example:

- `?debug_aqi=1`
- or `window.UK_AQ_DEBUG_AQI_BANDS = true`

Debug output should show:

- selected AQI source sensor
- `timeseries_id`
- `station_id`
- pollutant
- chart range
- calculated AQI chunk ranges
- requested AQI URLs
- response status
- response metadata
- raw row count
- parsed point count
- DAQI count
- EAQI count
- gap ranges after parsing
- cache hit/miss
- ranges marked covered
- ranges marked failed
- rendered DAQI segment count
- rendered EAQI segment count

This should make it possible to compare:

- R2 Dropbox backup data
- AQI history endpoint response
- frontend parsed points
- rendered SVG segments

## Expected fetch sequence examples

### Example A: fresh 90 day chart, one sensor selected

1. User opens chart mode.
2. Primary sensor is selected.
3. AQI source sensor becomes the primary sensor.
4. Create chart frame.
5. Build AQI chunk queue for the full 90 day range.
6. Start AQI R2 chunk requests for the historical and one-day-overlap ranges, newest first.
7. Do not request AQI from R2 for the retention range.
8. Fetch AQI for the retention range from obsaqidb.
9. For the one-day overlap, fill AQI hours missing from R2 using obsaqidb.
10. Render DAQI/EAQI chunks as responses arrive.
11. Build observation request plan:
   - R2 for the historical range
   - R2 preferred for the one-day overlap
   - ingestdb only for missing one-day-overlap observation hours
   - ingestdb directly for the retention range
12. Fetch/render primary sensor line, newest chunks first.
13. Keep cache for future range changes.

### Example B: user expands from 7 days to 90 days

1. Keep existing 7 day AQI bands and line chart visible.
2. Detect missing older AQI range.
3. Fetch missing older AQI chunks, newest missing chunk first.
4. Detect missing older observation range.
5. Fetch missing older observation chunks, newest missing chunk first.
6. Merge into existing cache and render without clearing current chart.
7. Do not refetch already covered 7 day data.

### Example C: user contracts from 90 days to 7 days

1. Do not refetch data.
2. Update x-domain.
3. Clip/filter existing cached points to the visible range.
4. Re-render AQI bands and lines for the smaller range.
5. Keep the larger cached range available for quick re-expansion.

### Example D: user selects a second sensor

1. Keep current AQI bands from the first sensor.
2. Fetch observation history for the second sensor.
3. Render second line as chunks arrive.
4. After observation fetch is underway or complete, prefetch AQI history for the second sensor in the background.
5. Do not redraw AQI bands unless the user chooses the second sensor as the AQI source.

### Example E: user changes AQI source sensor

1. Keep line chart unchanged.
2. Check AQI cache for the newly selected AQI source sensor.
3. If cached, render AQI bands immediately.
4. If not cached, fetch AQI chunks newest first.
5. Render AQI bands as chunks arrive.

## API contract requirements

### AQI history endpoint should return

For each AQI row or segment:

- UTC start timestamp
- `timeseries_id`
- `station_id`, if available
- `pollutant_code`
- DAQI index level
- EAQI index level

The frontend should accept generic AQI fields:

- `period_start_utc` or `timestamp_hour_utc`
- `daqi_index_level`
- `eaqi_index_level`

It may also accept worker-style pollutant-specific fields for compatibility:

- `daqi_pm25_rolling24h_index_level`
- `eaqi_pm25_index_level`
- `daqi_pm10_rolling24h_index_level`
- `eaqi_pm10_index_level`
- `daqi_no2_index_level`
- `eaqi_no2_index_level`

### Observation history endpoint should return

For each observation row:

- UTC timestamp
- `timeseries_id`
- pollutant
- value
- source or connector identity if useful
- metadata showing whether the row came from R2 or ingestdb, if available

### Response metadata should ideally include

- requested range
- returned range
- source coverage
- missing ranges
- R2 row count
- ingestdb row count for observation history
- obsaqidb row count for AQI retention-range fallback
- errors
- partial response flag

## R2, ingestdb, and obsaqidb access impact

### R2 reads

This plan increases perceived responsiveness but should not increase total R2 reads unnecessarily if caching and in-flight request de-duplication are used.

AQI bands:

- fresh chart opens may issue multiple parallel AQI R2 reads
- total read count should be the same as sequential chunk fetching
- concurrency changes timing, not total reads

Observation lines:

- R2 is preferred for history
- R2 is not queried repeatedly for already covered ranges
- R2 should not be queried for old ranges that are already cached

### ingestdb reads

ingestdb should only be used for observation line data in:

- the retention range directly
- missing observation hours in the one-day overlap

This keeps ingestdb reads bounded even for 31 day and 90 day chart ranges.

For older ranges, ingestdb must not be queried.

ingestdb should not be used for AQI bands in this plan.

### obsaqidb reads

obsaqidb should only be used for AQI band data in:

- the retention range directly
- missing AQI hours in the one-day overlap

For AQI bands:

- do not query R2 for the retention range
- query obsaqidb directly for the retention range
- query R2 first for the one-day overlap
- identify missing AQI hours inside the one-day overlap
- query obsaqidb only for those missing one-day-overlap AQI hours
- do not query obsaqidb for historical AQI older than the one-day overlap
- do not query obsaqidb for observation line data

This keeps obsaqidb reads bounded and prevents 31 day or 90 day charts from causing large obsaqidb reads.

### R2 writes

This plan does not require additional R2 writes.

Any future plan to precompute compact AQI band strips would add R2 writes, but that is out of scope here.

## Non-goals

This plan does not include:

- using obsaqidb for chart observation lines
- using obsaqidb for AQI outside the retention range and one-day overlap
- client-side production AQI calculation
- changing the current chart range expand/contract behaviour
- changing the selected sensor limit
- changing the AQI colour definitions
- precomputing compact AQI band strips into new R2 objects
- changing the map averaging/window logic

## Acceptance criteria

### Fresh chart load

- AQI bands for the primary sensor start loading first.
- AQI chunks are fetched in parallel.
- AQI bands appear from newest to oldest where data is available.
- Primary sensor line chart then appears from newest to oldest.
- The chart remains usable while data is loading.

### Range default and persistence

- Chart range defaults to `24h` when chart mode opens for a newly selected hex.
- If the user leaves chart mode and returns without selecting a different hex, the last selected chart range persists.
- If the user selects a different hex, the chart range resets to `24h`.
- Returning to a previous hex after selecting a different hex also resets the chart range to `24h`.
- The chart range control always visually matches the active chart-session range.

### Range changes

- Expanding range fetches only missing intervals.
- Contracting range does not refetch.
- Existing working expand/contract behaviour is preserved.
- Existing visible data is not wiped unnecessarily.

### Additional sensors

- Selecting another sensor renders that sensor’s line as soon as its observation data is available.
- Selecting another sensor does not change the AQI bands.
- AQI history for the added sensor is prefetched in the background.
- Switching AQI source to a prefetched sensor displays bands immediately.

### Data source correctness

- R2 is preferred wherever available.
- R2 is never queried for observations or AQI inside the retention range.
- ingestdb is used for observation line data inside the retention range.
- ingestdb is used only for missing observation line data in the one-day overlap.
- obsaqidb is used for AQI band data inside the retention range.
- obsaqidb is used only for missing AQI band data in the one-day overlap.
- obsaqidb is not used for observation lines.
- Failed or malformed responses do not poison the covered range cache.

### AQI gap debugging

- Debug mode can show whether AQI gaps come from:
  - missing R2 data
  - API response gaps
  - frontend parser drops
  - cache coverage mistakes
  - SVG rendering logic

## Suggested implementation phases

### Phase 1: document and instrument current behaviour

- Add debug logging behind a flag.
- Log actual AQI request URLs, response counts, parsed counts, and rendered segment counts.
- Log observation fetch plans and source decisions.
- Do not change user-facing behaviour yet.

### Phase 2: formalise chart session and fetch planning

- Add an explicit chart session state keyed by selected hex identity.
- Default chart range to `24h` for new selected-hex sessions.
- Preserve last selected range only while the selected hex has not changed.
- Build explicit fetch plans for AQI and observations.
- Separate source decision from rendering.
- Add cache records for covered, failed, and in-flight ranges.
- Preserve current expand/contract behaviour.

### Phase 3: enforce AQI-first fresh load

- On fresh chart load, start AQI source fetches first.
- Fetch AQI chunks in parallel.
- Render AQI bands incrementally from newest to oldest.
- Start observation line fetches after AQI fetch queue has started.

### Phase 4: enforce source rules

- R2 preferred for all historical observations outside the retention range.
- R2 preferred for AQI bands outside the retention range wherever available.
- never fetch R2 for observations or AQI inside the retention range.
- ingestdb used directly for retention-range observation data.
- ingestdb used only for missing one-day-overlap observation data.
- obsaqidb used directly for retention-range AQI band data.
- obsaqidb used only for missing one-day-overlap AQI band data.
- no obsaqidb for observation line data.

### Phase 5: selected sensor AQI prefetch

- When extra sensors are selected, render lines immediately.
- Prefetch AQI history for those sensors in the background.
- Use cached AQI if the user switches AQI source.

## Questions for implementation

1. Where is the current chart observation endpoint defined?
2. Does the chart observation endpoint already return source metadata showing R2 vs ingestdb?
3. Where is `ingest_retention_days` exposed to the frontend or cache proxy?
4. Does the AQI history endpoint accept `timeseries_id` only, or does it require `station_id` too?
5. Does the AQI history endpoint already merge R2 AQI with obsaqidb retention-range AQI, or does that need to be added?
6. Does the AQI history endpoint return source metadata for R2 versus obsaqidb rows?
7. Does the AQI history endpoint return generic `daqi_index_level` and `eaqi_index_level`, or worker-style pollutant-specific fields?
8. What exact hex identity should be used for chart range persistence, for example constituency code, local authority code, or internal cell key?
9. Should AQI and observation chunk sizes be the same?
10. What concurrency limits should be used for AQI history and observation history?
11. Should debug output be console-only, or should there be a temporary on-page debug panel?

## Recommended default decisions

Unless the codebase shows a better reason:

- Default chart range to `24h` for a newly selected hex.
- Preserve the last selected chart range only while the selected hex has not changed.
- Use 3 or 4 concurrent AQI chunk requests.
- Render AQI chunks as each chunk completes.
- Use newest-to-oldest ordering for missing chunk queues.
- Keep current range expand/contract behaviour.
- Use R2-preferred source merging.
- Never fetch R2 for observations or AQI inside the retention range.
- Use ingestdb directly for observation line data in the retention range.
- Use ingestdb only for missing observation line data in the one-day overlap.
- Use obsaqidb directly for AQI band data in the retention range.
- Use obsaqidb only for missing AQI band data in the one-day overlap.
- Do not use obsaqidb for observation lines.
- Do not mark failed or empty responses as covered.
- Keep AQI source separate from selected line sensors.
