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
