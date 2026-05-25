# Hex Map Sensor List + Chart Mode Redesign Plan

## Purpose

Create a clear implementation plan for Codex to redesign the `hex_map.html` sensor list and chart mode UI.

This is a design and investigation prompt. Codex should inspect the existing code before implementing, avoid assumptions, and keep changes safe and incremental.

## Source file

Primary file to investigate:

- `hex_map.html`

## Overall goals

- Make the sensor list feel consistent between map mode and chart mode.
- Keep the selected area/hex context clear.
- Make chart mode feel like a focused sensor-analysis view, not a second map-navigation view.
- Remove layout jumps between modes.
- Improve chart rendering so changing chart range uses cached data and animates existing data instead of blanking/rebuilding unnecessarily.
- Keep the visual language simple: AQ colours only mean readings/air-quality categories; chart identity uses the standard UK AQ blue.

---

# Locked design decisions

## 1. Sensor list must be uniform across map mode and chart mode

The sensor list should use one consistent visual structure across both modes.

### Requirements

- The headers must stay in the same position between map mode and chart mode.
- The column widths should not jump when switching mode.
- Map mode must reserve the same left-side space used by chart mode for selection/symbol/icon affordances.
- The sensor list must not shift vertically or horizontally when entering or leaving chart mode.
- Fix any existing jump where the sensor list changes position between chart and map mode.

### Codex investigation

Inspect the current map-mode and chart-mode sensor table implementations. Determine whether they are duplicated, separately styled, or using hidden columns that cause layout changes. Refactor or align them so the same layout rules apply consistently.

---

## 2. Remove the Window column

The current `Window` column should be removed from the sensor table.

Instead of showing each row as `Included` / `Outside window`, group the rows visually.

### Requirements

- Sensors inside the selected averaging window appear first.
- Sensors outside the selected averaging window appear at the bottom.
- Insert a half-height divider row between the groups.
- Divider text should be capitals with down arrows either side:

```text
↓ OUTSIDE WINDOW ↓
```

- The divider should be visually lighter than normal rows and clearly not a selectable sensor.
- Outside-window rows remain visible and selectable for charting.
- Changing the Window selector may move sensors above/below this divider.

---

## 3. Fix sensor list filtering bug

The list appears to show only sensors inside the current window, rather than all sensors for the selected area/hex.

### Requirements

- The sensor list should show all sensors belonging to the selected area/hex, subject only to selected network/pollutant visibility rules that are already intended.
- Sensors outside the current window must not be dropped; they should be shown in the `OUTSIDE WINDOW` group.
- Codex should investigate whether the filtering bug is caused upstream before render, during visible-entry calculation, by the current window filter, or by chart-mode-specific logic.

---

## 4. Chart mode should hide map-navigation controls

Chart mode is a focused analysis view for the already-selected area.

### Hide in chart mode

- Map search bar.
- Network selector / network pill / network panel.
- Map zoom controls.
- Map settings controls.
- Map legend.
- Any control that implies map exploration.

### Keep in chart mode

- Back to map button.
- Pollutant selector.
- Window selector.
- Chart range selector.
- Sensor list.
- Sensor chart.

### Reasoning

Search and network selection are map exploration/filter controls. Leaving them visible in chart mode creates ambiguity about whether they will change the selected area, remove sensors, or invalidate the current chart comparison.

---

## 5. Window selector behaviour in chart mode

The Window selector should remain visible in chart mode.

### Requirements

Window selector changes should affect:

- The selected area/hex reading in the sensor list title/header.
- The selected area/hex colour shown in the sensor list title/header.
- Which sensors are grouped inside vs outside the current window.
- The ordering/group position of sensors in the list.

Window selector changes should **not** affect:

- The selected sensor chart header reading/dot directly.
- The chart historical range.

### Naming

- Keep toolbar control as `Window`.
- Rename the chart's previous `Time Range` control to `Chart range`.

### Conceptual distinction

- `Window` = current area/hex reading context and sensor-list inclusion grouping.
- `Chart range` = historical time span shown in the chart.

---

## 6. Area/hex title behaviour

The area/hex name stays in the sensor list title/header.

### Map mode

- Clicking the area/hex name opens chart mode.
- Preserve the current behaviour: opening chart mode from the area/hex title selects the top sensor by default.
- The chart icon next to the area/hex title should also open chart mode with the top sensor selected.

### Chart mode

- The area/hex name must not be clickable.
- The area/hex chart icon should disappear in chart mode.
- The area/hex name must not move when the icon disappears. Reserve space or otherwise avoid any layout shift.

---

## 7. Sensor row chart affordance

### Recommendation to implement

Do **not** make the whole sensor row open chart mode.

Instead:

- In map mode, show a chart icon to the left of the sensor name area on row hover/focus.
- Hovering anywhere in the row should reveal the chart icon.
- Clicking the chart icon opens chart mode with that sensor selected.
- The row itself should not unexpectedly switch to chart mode, because that could conflict with sorting, selecting, focusing, or future row interactions.
- In chart mode, use the reserved left-side area for chart selection/symbol controls.

### Reasoning

A dedicated icon is more explicit and avoids accidental chart-mode entry while the user is scanning or interacting with the list.

---

## 8. Red cross behaviour

Use distinct meanings for `Back to map` and the red cross.

### Back to map

- Leave chart mode.
- Return to map mode.
- Keep the currently selected hex/area and sensor list open.

### Red cross in chart mode

- Clear the selected hex/area.
- Close the sensor list.
- Exit chart mode.
- Return to the plain map state.

### Red cross in map mode

- Close the sensor list / clear the selected area, as currently expected.

---

# Chart title/header design

## 9. Chart title should be sensor-led

The chart title should no longer be the area/hex title.

### One selected sensor

Display:

```text
Sensor Name
Network Name · [AQ coloured dot] Current PM2.5: 12.3 µg/m³ · Updated 14:32
```

### Multiple selected sensors

The first selected sensor remains the lead title:

```text
Sensor Name
Network Name · [AQ coloured dot] Current PM2.5: 12.3 µg/m³ · Updated 14:32
Comparing with 2 sensors
```

### Timestamp format

- Same day: `Updated 14:32`
- Yesterday: `Updated yesterday 23:10`
- Older: `Updated 22 May, 14:32`

### AQ dot placement

The AQ coloured dot must stay immediately to the **left of the current reading**, not next to the sensor name.

### Colour meaning

AQ colours are reserved for readings / air-quality categories only.

---

# Chart selection and symbols

## 10. Maximum selected sensors

Limit chart comparison to a maximum of 4 selected sensors.

Codex should enforce this in the UI and show a gentle message if the user tries to select a fifth sensor.

Suggested message:

```text
You can compare up to 4 sensors.
```

## 11. Chart symbols

Do not use a circle symbol, because it clashes with:

- selection radio dots;
- AQ coloured reading dots.

Use these symbols:

1. Square
2. Triangle
3. Diamond
4. Star

Do not use cross/plus.

### Symbol consistency

- The symbol in the sensor list and the marker on the chart must match exactly.
- Avoid using a text glyph in one place and an SVG path in another if that causes visible mismatch.
- Prefer a shared symbol renderer or shared SVG/path definitions.
- Fix the existing diamond mismatch between chart and sensor list.

## 12. Chart line and symbol colours

Use the standard UK AQ blue for chart identity.

### Requirements

- Do not use red, green, yellow, or orange for chart lines or chart symbols, because those clash with AQ reading colours.
- Use standard blue for chart lines/symbols.
- Black may be used only if needed for contrast or non-primary chart identity, but the default should be the standard blue.
- If multiple sensors need distinction, prefer symbols and line style/weight/opacity rather than AQ-like colours.

## 13. Symbol sizing

Codex should review chart symbol size.

### Direction

- Chart symbols should probably be slightly larger than the current implementation.
- Keep them large enough to identify, but not so large that they clutter the line chart.
- Sensor-list symbols should remain visually aligned and easy to scan.

---

# Chart interaction polish

## 14. Hover behaviour for chart lines

When hovering a line on the chart:

- Grey out / de-emphasise the other lines.
- Make the hovered line slightly larger/thicker.
- Keep the hovered line's symbols/markers prominent.
- Restore normal appearance on pointer leave.

This should make multi-sensor comparison easier to understand.

## 15. Tooltip behaviour

For multi-line charts, the tooltip should clearly identify the relevant sensor.

Include:

- symbol;
- sensor name;
- value;
- timestamp.

Keep it compact.

## 16. Empty state

When chart mode opens with no selected sensor, show a calm empty state rather than an error.

Suggested message:

```text
Select a sensor from the list to draw a chart.
```

Note: opening chart mode from the area/hex title should preserve current behaviour and select the top sensor by default. The empty state is still useful for edge cases where no sensor is selected or the selected sensor is removed.

---

# Chart range rendering and caching

## 17. Do not blank/redraw data unnecessarily

Changing `Chart range` should feel like zooming/compressing/uncompressing the timeline, not blanking and rebuilding the chart.

### Current problem to investigate

When changing from, for example, 24 hours to 7 days, the chart blanks and redraws the last 24 hours again, even when that data is already present in the browser.

### Requirements

1. Do not request data already loaded in the browser.
2. If the browser has 7 days loaded and the user switches to 24 hours, slice/filter existing cached data.
3. If the browser has 24 hours loaded and the user switches to 7 days, request only the missing older range, not the overlapping 24 hours again.
4. If the requested sensor/pollutant/range data is already cached, use it.
5. Do not blank existing line data or AQI background bands during range changes.
6. Existing data should animate/compress/expand as the x-axis domain changes.
7. Newly loaded older data should extend into view once available.
8. AQI background bands/stripes should remain stable and not flicker.
9. Loading indication should only appear for genuinely missing data, and should not obscure already-rendered data unless there is no existing chart data at all.

### Codex investigation

Inspect existing chart cache keys, range handling, fetch chunk logic, and redraw/animation flow. Determine whether current caching is keyed too narrowly by range, whether `loadToken` invalidation causes full rebuilds, and whether `updateChart` clears existing SVG elements unnecessarily.

---

# Phased implementation plan

## Phase 1 — Investigation and current-state map

Codex should first inspect the existing implementation and produce a brief findings summary before coding.

### Deliverables

- Identify all functions/classes/DOM sections involved in:
  - map-mode sensor list rendering;
  - chart-mode sensor list rendering;
  - chart mode enter/exit;
  - area-title click behaviour;
  - chart series fetching and caching;
  - chart range changes;
  - symbol rendering;
  - row selection and selected-sensor state.
- Explain why the sensor list currently jumps between modes.
- Explain why outside-window sensors appear to be filtered out.
- Explain why chart range changes blank/redraw existing data.
- Recommend any safe refactor boundaries before implementing.

### Codex prompt

```text
You are working in the UK AQ hex map UI. Do not jump straight to implementation.

Investigate `hex_map.html` and map the current implementation for:
- map-mode sensor list rendering;
- chart-mode sensor list rendering;
- chart mode enter/exit;
- area/hex title click behaviour;
- chart series fetching/caching;
- chart range changes;
- symbol rendering;
- selected sensor state.

Please produce a concise findings summary before coding. Specifically answer:
1. Why does the sensor list sometimes jump between map mode and chart mode?
2. Where are sensors outside the selected Window being filtered or dropped?
3. Why does changing Chart range blank/redraw data that is already loaded?
4. Which parts can be safely refactored without changing unrelated map behaviour?

Do not implement until the findings are clear.
```

---

## Phase 2 — Sensor list structure and outside-window grouping

### Deliverables

- Uniform sensor list layout across map and chart mode.
- Reserved left-side icon/select/symbol space in map mode and chart mode.
- Removed Window column.
- Inside-window and outside-window grouping.
- Half-height `↓ OUTSIDE WINDOW ↓` divider.
- All sensors for selected area shown, including outside-window sensors.
- No sensor list jump between modes.

### Codex prompt

```text
Implement the sensor list redesign in `hex_map.html`.

Requirements:
- Make the sensor list layout uniform across map mode and chart mode.
- Keep headers and columns in the same positions between modes.
- Reserve left-side space in map mode for the chart icon/select/symbol area so columns do not shift when entering chart mode.
- Remove the Window column.
- Show sensors inside the selected Window first.
- Show sensors outside the selected Window at the bottom.
- Insert a half-height divider row labelled `↓ OUTSIDE WINDOW ↓` between the groups.
- Outside-window sensors must remain visible and selectable for charting.
- Fix the existing issue where the list appears to show only inside-window sensors instead of all sensors for the selected area.
- Prevent sensor list vertical/horizontal jumping when switching between map and chart modes.

Do not change unrelated map, network, or chart behaviour in this phase except where necessary for the list.
```

---

## Phase 3 — Chart mode controls and area/header behaviour

### Deliverables

- Hide search and network controls in chart mode.
- Keep pollutant, Window, Chart range, Back to map.
- Rename Time Range to Chart range.
- Window selector updates area/hex title reading/colour and list grouping, not the selected sensor chart header.
- Area title behaviour:
  - map mode: clickable and opens chart mode with top sensor selected;
  - chart mode: not clickable;
  - chart icon disappears in chart mode without moving the title.
- Red cross behaviour implemented as specified.

### Codex prompt

```text
Implement the chart-mode control/header behaviour in `hex_map.html`.

Requirements:
- In chart mode, hide map search and network selector/pill/panel controls.
- Continue hiding map zoom/settings/legend controls in chart mode as appropriate.
- Keep visible: Back to map, pollutant selector, Window selector, Chart range selector, sensor list, chart.
- Rename the chart control label from `Time Range` to `Chart range`.
- Keep the Window selector visible in chart mode.
- Window changes should update the selected area/hex reading and colour in the sensor list title/header, and regroup sensors inside/outside the window.
- Window changes should not directly change the selected sensor chart header reading/dot.
- Preserve existing behaviour where clicking the area/hex title in map mode opens chart mode with the top sensor selected.
- The area/hex chart icon should also open chart mode with the top sensor selected.
- In chart mode, the area/hex name must not be clickable.
- In chart mode, the area/hex chart icon should disappear, but the area/hex title must not move.
- Back to map should exit chart mode but keep the selected area and sensor list open.
- The red cross in chart mode should clear the selected area, close the sensor list, exit chart mode, and return to the plain map.

Keep changes local to chart-mode UI state and selected-area handling.
```

---

## Phase 4 — Sensor row chart affordance and selection limit

### Deliverables

- Chart icon appears to the left of sensor name on row hover/focus in map mode.
- Hovering anywhere in the row reveals the icon.
- Clicking the icon opens chart mode with that sensor selected.
- Whole row does not open chart mode.
- Maximum of 4 selected sensors in chart mode.
- Gentle message when attempting to select a fifth sensor.

### Codex prompt

```text
Implement the sensor-row chart affordance and selected-sensor limit.

Requirements:
- In map mode, show a chart icon to the left of the sensor name area when hovering or focusing anywhere in that sensor row.
- The reserved icon/select/symbol column should already exist from the sensor list layout work; use it.
- Clicking the chart icon opens chart mode with that sensor selected.
- Do not make the whole row open chart mode.
- Preserve normal row/text interactions and accessibility.
- In chart mode, allow a maximum of 4 selected sensors.
- Use a gentle message if the user attempts to select a fifth sensor: `You can compare up to 4 sensors.`

Avoid changing chart data fetching in this phase.
```

---

## Phase 5 — Chart header and symbols

### Deliverables

- Sensor-led chart title/header.
- AQ coloured dot stays left of current reading.
- Timestamp formatting rules implemented.
- Symbols changed to square, triangle, diamond, star.
- No circle and no cross/plus.
- Diamond appears identical in sensor list and chart.
- Standard UK AQ blue used for chart line/symbol identity.
- No red/green/yellow/orange chart identity colours.

### Codex prompt

```text
Implement the chart header and symbol redesign.

Requirements:
- Chart title/header should be led by the first selected sensor, not by the area/hex name.
- For one selected sensor, show:
  Sensor Name
  Network Name · [AQ coloured dot] Current PM2.5: 12.3 µg/m³ · Updated 14:32
- For multiple selected sensors, keep the first selected sensor as the lead and add a compact line such as `Comparing with 2 sensors`.
- AQ coloured dot must appear immediately to the left of the current reading, not next to the sensor name.
- Timestamp formatting:
  - Same day: `Updated 14:32`
  - Yesterday: `Updated yesterday 23:10`
  - Older: `Updated 22 May, 14:32`
- Use symbols in this order: square, triangle, diamond, star.
- Do not use circle or cross/plus symbols.
- Ensure the list symbol and chart marker are visually identical, preferably via shared SVG/path rendering.
- Fix the current diamond mismatch between the chart and sensor list.
- Use the standard UK AQ blue for chart lines and symbols.
- Do not use red, green, yellow, or orange for chart lines/symbols because those colours are reserved for AQ reading categories.
- Review symbol sizing and make chart markers slightly more legible if needed without cluttering the chart.

Keep AQ colours reserved for current readings / air-quality category dots only.
```

---

## Phase 6 — Chart range caching and animated range changes

### Deliverables

- Chart range changes do not blank existing data.
- Browser cache is reused where possible.
- Only missing date ranges are fetched.
- AQI bands/stripes do not flicker.
- Existing lines compress/uncompress during range changes.
- Newly loaded older data extends into view when available.

### Codex prompt

```text
Improve chart range caching and rendering.

Current problem:
Changing Chart range, such as 24 hours to 7 days, blanks the chart and redraws existing data/AQI bands even when the browser already has overlapping data.

Requirements:
- Do not request data already loaded in the browser.
- If a wider range is requested, fetch only the missing older/newer range, not overlapping data already cached.
- If a narrower range is requested, slice/filter existing cached data.
- Cache should be keyed so data can be reused across chart ranges for the same sensor/pollutant/window context where valid.
- Do not blank existing chart lines during Chart range changes.
- Do not blank or flicker AQI coloured bands/stripes during Chart range changes.
- Animate x-axis domain changes so the chart feels like it compresses/uncompresses over time.
- Existing data should remain visible during range changes.
- Newly loaded missing data should appear/extend the series once available.
- Loading state should not obscure existing chart data unless there is no existing data to show.

Please inspect the current cache keys, fetch chunk logic, load token invalidation, and SVG update/clear behaviour before changing the implementation.
```

---

## Phase 7 — Chart interaction polish

### Deliverables

- Hovering a chart line greys out/de-emphasises other lines.
- Hovered line becomes slightly thicker/larger.
- Tooltip clearly identifies sensor, symbol, value, timestamp.
- Empty state for no selected sensor.
- Scroll position preserved where possible when Window changes regroup rows.

### Codex prompt

```text
Implement chart interaction polish.

Requirements:
- When hovering a line on a multi-sensor chart, grey out or de-emphasise the other lines.
- Make the hovered line slightly thicker/larger and keep its markers prominent.
- Restore normal styling on pointer leave.
- Tooltip should clearly identify the relevant sensor and include: symbol, sensor name, value, timestamp.
- If chart mode has no selected sensor, show a calm empty state: `Select a sensor from the list to draw a chart.`
- Preserve sensor-list scroll position where possible when Window changes only regroup rows inside/outside the current window.

Keep the design simple and avoid adding new visual clutter.
```

---

# Acceptance checklist

- [ ] Sensor list headers do not jump between map and chart mode.
- [ ] Sensor list position does not jump between map and chart mode.
- [ ] Window column removed.
- [ ] Outside-window sensors are visible under `↓ OUTSIDE WINDOW ↓`.
- [ ] All selected-area sensors appear unless excluded by intended network/pollutant filters.
- [ ] Search bar hidden in chart mode.
- [ ] Network selector hidden in chart mode.
- [ ] Window selector visible in chart mode.
- [ ] Time Range renamed to Chart range.
- [ ] Window changes update area/hex title reading/colour and row grouping.
- [ ] Window changes do not directly change selected sensor chart header reading/dot.
- [ ] Area title opens chart mode with top sensor selected in map mode.
- [ ] Area title is not clickable in chart mode.
- [ ] Area chart icon disappears in chart mode without moving the area title.
- [ ] Back to map keeps selected area/sensor list open.
- [ ] Red cross clears selected area and exits chart mode.
- [ ] Map-mode row hover/focus reveals chart icon.
- [ ] Whole row does not open chart mode.
- [ ] Maximum of 4 selected sensors enforced.
- [ ] Symbols are square, triangle, diamond, star.
- [ ] No circle or cross/plus symbols.
- [ ] Sensor-list and chart symbols match exactly.
- [ ] Chart identity uses standard UK AQ blue; no red/green/yellow/orange lines or symbols.
- [ ] Chart range changes reuse cached data.
- [ ] Chart range changes do not blank existing lines or AQI bands.
- [ ] Chart range changes animate as compress/uncompress timeline changes.
- [ ] Hovering a chart line de-emphasises other lines and emphasises the hovered line.
- [ ] Tooltip clearly identifies sensor, symbol, value, timestamp.
