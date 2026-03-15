# Codex Prompt: Replace AQI metric switching with DAQI and EAQI colour bands

Task: update `uk_aq_stations_chart.html` to remove AQI metric switching and replace it with two always-visible hourly AQI colour bands between the loading timeline and the main observations chart.

Work only in this file unless there is a very strong reason not to.

## Current page context

- The chart range is controlled by `#window-select`.
- The main observations chart is rendered by `renderSeriesChart(points, meta, windowLabel, guideline)`.
- Observations are loaded by `loadObservationSeriesData(windowValue)`.
- AQI history is currently loaded by `loadAqiSeriesData(windowValue, metric)`.
- `loadSeriesData()` currently switches between observations / DAQI / EAQI based on the metric dropdown state.
- AQI request URLs are built by `buildAqiHistoryRequestCandidates(stationId, windowValue)`.
- AQI points are currently parsed via `parseAqiHistoryPoints(payload, metric)`.
- The page already has a chart-local loading pattern and chart wrapper structure.

## Goal

Change the chart UI so that:

1. the metric dropdown is removed completely
2. the observations chart is always the main chart
3. two compact hourly AQI colour bands are always shown above the observations chart
4. the AQI bands are:
   - DAQI band
   - EAQI band
5. the AQI bands share the exact same time range and x alignment as the observations chart
6. hours with no AQI data show as light grey
7. the AQI bands sit between the loading timeline and the main chart, not below the chart

## Final visual order

Inside the chart area, top to bottom:

1. existing loading timeline bar
2. DAQI hourly colour band
3. EAQI hourly colour band
4. main observations chart

## Important layout requirements

- Keep the AQI bands full chart width and aligned to the same drawable time axis as the observations chart.
- AQI bands should be shallow strips, not mini charts.
- Suggested starting height:
  - each AQI band about `22px` tall
- Keep a small gap between the two AQI bands.
- Keep a slightly larger gap between the AQI bands block and the main chart.
- Label the bands on the left as:
  - `DAQI`
  - `EAQI`
- Preserve responsiveness.

## Remove old metric UI and logic

- Remove the metric dropdown from the DOM/UI completely.
- Remove any event handling only used for chart metric switching.
- Remove the observations vs DAQI vs EAQI mode switch in `loadSeriesData()`.
- `loadSeriesData()` should always load and render:
  - observations for the main chart
  - DAQI band data
  - EAQI band data
- Keep the range selector (`#window-select`).
- Do not break station selection, refresh behaviour, tooltip behaviour, fixed date range behaviour, or loading timeline behaviour.

## AQI data requirements

- Reuse the existing AQI history endpoint/request-building logic where possible.
- Continue to use `buildAqiHistoryRequestCandidates(stationId, windowValue)` as the starting point.
- You may refactor AQI loading so a single AQI payload can populate both DAQI and EAQI bands if the endpoint already returns both.
- Avoid making unnecessary duplicate requests if one response contains both standards.
- If separate parsing paths are needed, keep them clean and explicit.

## Implement a new AQI band data layer

Create or refactor helper functions along these lines:

- `loadAqiBandsData(windowValue)`
- `parseAqiBandPayload(payload)`
- `renderAqiBands(containerOrSvg, bandState)`
- `buildHourlyBandCells(...)`
- `getDaqiBandColor(...)`
- `getEaqiBandColor(...)`
- `getNoDataBandColor()`

You do not need to use these exact names, but keep the logic separated and readable.

## Band semantics

The AQI bands should show one colour block per hour segment across the requested time range.
Each hour slot must be rendered independently.

### DAQI band rules

- Use DAQI colours by index level.
- Treat `0` or missing as no data and render light grey.

Use this DAQI palette:

- `0` or missing: light grey
- `1`: `#BED82F`
- `2`: `#62BB3D`
- `3`: `#358A2F`
- `4`: `#F2BE1C`
- `5`: `#FA9418`
- `6`: `#F1671E`
- `7`: `#ED1B24`
- `8`: `#B50F19`
- `9`: `#72361A`
- `10`: `#B83D97`

### EAQI band rules

- Use EAQI colours by named band/category or equivalent numeric/category mapping from the payload.
- Treat `0` or missing as no data and render light grey.

Use this EAQI palette:

- `0` or missing: light grey
- `Good`: `#50F0E6`
- `Fair`: `#50CCAA`
- `Moderate`: `#F0E641`
- `Poor`: `#FF5050`
- `Very poor`: `#960032`
- `Extremely poor`: `#7D2181`

If the payload exposes EAQI as numeric codes rather than names, map them consistently into the 6 categories above.

## No-data handling

- Use a single light grey for no data, for example `#D9D9D9`.
- No-data styling must apply when:
  - the AQI value is `null`
  - the AQI value is missing
  - the AQI value is `0`
  - the hour is absent from the payload after alignment/filling
- Fill the requested time range into hourly slots so the bands remain continuous across the whole chart width.

## Time alignment requirements

- Both AQI bands must align exactly to the same time domain as the observations chart.
- If needed, create a shared x domain / shared hourly slot generator from the active window.
- The bands should visually line up with the chart’s x-axis positions.
- For `24h`, `7d`, `30d/31d`, and `90d`, the AQI cell layout must stay stable and correctly aligned.
- If the chart uses a custom/fixed date range, the AQI bands must align to that too.

## Rendering requirements

- Render the AQI bands as thin horizontal strips made of adjacent hourly cells.
- No gaps between hourly cells unless a tiny gap is required for rendering clarity.
- Keep the AQI bands visually secondary to the main chart.
- Do not render AQI as lines or area charts.
- The observations chart remains the primary visual focus.

## Hover and interaction

- Preserve the main chart tooltip.
- If practical without overcomplicating the page, add hover sync so hovering a time in the chart can also highlight the corresponding AQI hour segment.
- This is optional. Do not let it derail the main implementation.
- Do not add a second heavyweight tooltip unless it is clearly useful.

## Loading behaviour

- Keep the existing chart-local loading timeline.
- While the selected range is loading:
  - the loading timeline should still function
  - the AQI bands should update when their data is available
- Do not block rendering of the observations chart waiting on AQI if the observations are ready first.
- Do not add a full-page spinner.
- Handle AQI failures gracefully:
  - if AQI fails, keep the observations chart working
  - show all-grey AQI bands or a settled empty state rather than breaking the chart

## Accessibility and clarity

- Do not rely on colour alone in code structure or semantics.
- Add accessible labels/ARIA text for the DAQI and EAQI bands.
- Keep labels readable on dark and light themes if applicable.
- Avoid clutter.

## Implementation notes

- Prefer updating DOM/SVG in place rather than tearing down everything unnecessarily.
- Keep CSS additions near existing chart styles.
- Keep the code modular and easy to extend.
- Do not introduce a framework.
- Do not change unrelated functionality.

## Acceptance criteria

1. The metric dropdown no longer appears anywhere in the chart UI.
2. The chart always shows observations as the main chart.
3. A DAQI colour band is shown between the loading timeline and the observations chart.
4. An EAQI colour band is shown directly below the DAQI band.
5. Both AQI bands use the exact palettes specified above.
6. Missing/0 AQI hours render as light grey.
7. AQI bands span the same width and time range as the observations chart.
8. The AQI bands are visually shallow strips, around `22px` tall each.
9. Station switching still works.
10. Range switching still works.
11. The loading timeline still works.
12. The observations chart tooltip still works.
13. The page remains responsive.
14. If AQI data fails, the observations chart still renders.

## Output

After making the change, provide:

1. a short summary of what changed
2. whether AQI data was loaded with one request or multiple requests
3. any assumptions made about the AQI payload shape
4. any remaining limitations
