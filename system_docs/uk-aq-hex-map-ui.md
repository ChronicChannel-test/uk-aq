# UK-AQ Hex Map UI Notes

This document captures key UI state and data-flow conventions for `uk_aq_hex_map.html`.

## Page structure
- Two map panels live inside the map card: UK and Countries & Regions (C&R). Each panel has a header area, map canvas, legend, and summary card.
- Tabs switch panels; the pollutant picker is moved into the active header slot so it always sits under the title inside the card.

## Shared pollutant state
- Single source of truth: `activePollutant`.
- URL param: `pollutant=pm25|pm10|no2` is kept in sync with the UI.
- Pollutant UI: `#pollutant-selector` is a radiogroup with keyboard navigation and `aria-checked`.
- Tab switching does not change the pollutant; it only changes geometry/scope.

## Shared map settings
- Map settings (window, metric, color scale) are shared across tabs via `window.mapSettingsState`.
- `window.updateMapSettings()` dispatches a `mapsettingschange` event so both panels stay in sync.
- URL params `metric` and `color_scale` reflect the current selections.

## Rendering pipeline
- `renderMap()` (and helpers) takes the current pollutant + network selection and updates:
  - Map colors and "no data" fills for hexes without readings.
  - Legend label (pollutant + units).
  - Summary metrics (coverage, mean/median/highest/lowest).
- Pollutant filtering uses `getRowsForActivePollutant()` + `rowMatchesPollutant()`.
- PM2.5 outlier guard: `MAX_VALID_PM25_VALUE` is applied only for pm25 values.

## Loading/dimming behavior
- `setMapLoading(true)` adds `.map-wrap.is-loading` to dim the SVG during data refresh.
- `setMapLoading(false)` clears the dim after render.

## Pollutant caching
- `pollutantCache` stores latest rows per pollutant with a short TTL (`POLLUTANT_CACHE_TTL`).
- `applyCachedPollutant()` allows instant switching if data is fresh.

## Region selection (C&R)
- `activeRegion` drives the C&R map scope.
- URL param `map=` persists the active region in the address bar.

## Name source files (local)
- Display names for map areas are sourced from local geometry files in this repo, fetched directly by the browser.
- UK constituencies (PCON):
  - `data/PCON/uk-constituencies-2023.hexjson`
  - `data/PCON/uk-constituencies-2017.hexjson`
  - Name field: `hexes[<pcon_code>].n`
- Local authorities (C&R / LA):
  - `data/LAD/uk_aq_la_hex_2023.json`
  - Name field: `features[].properties.la_name`
  - Code field: `features[].properties.la_code`
- Supabase/cache responses provide metrics and station data; when name fields are null in those responses, map labels still resolve from the local geometry files above.

## Search/autocomplete
- The map topbar now uses a real combobox search UI (`.map-search`) in both UK and C&R panels.
- Endpoint config comes from URL params with defaults:
  - `postcode_suggest_url` (default `/api/postcode_suggest`)
  - `postcode_lookup_url` (default `/api/postcode_lookup`)
- Query behavior:
  - Postcode-like input (`B`, `BS2`, `SW1A`, etc.) calls postcode suggest.
  - Non-postcode text uses local in-memory indexes.
  - Local text matching starts at 1 char for constituency / local authority / sensor.
- Result groups and order:
  1. Postcode
  2. Constituency
  3. Local authority
  4. Sensor
  - Up to 2 per type first, then remaining slots fill in this same order up to 6 total.
- Selection routing:
  - Postcode result triggers exact lookup, then selects `pcon_code` on UK tab or `la_code` on C&R tab.
  - Constituency result switches to UK tab and selects PCON.
  - Local authority result switches to C&R tab and selects LA.
  - Sensor result selects containing PCON/LA based on active tab and available codes.
- C&R region fallback:
  - Local authority code-to-region lookup is built from `data/LAD/uk_aq_la_hex_2023.json`.
  - If an LA code is outside the current C&R region view, the map switches region and applies pending selection after the next load.

## Cache session auth
- Cache API calls now try the request first with `credentials: include`.
- A Turnstile-backed `POST /api/aq/session/start` is attempted only after a `401` response.
- Session expiry hints are shared across tabs in `localStorage` so quick multi-tab opens avoid redundant session minting.
- If a cache fetch fails with the browser-level Access/CORS pattern (`TypeError: Failed to fetch`), the page redirects to Cloudflare Access login for the current hostname and then returns to the same map URL.
