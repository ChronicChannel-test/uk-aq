Yes — this is big enough that I’d split it into two Codex Cloud prompts.

Reason: the first part is mostly layout/state movement, while the second part changes chart semantics by adding an explicit AQI-band source sensor. Doing both at once risks Codex mixing up “selected chart sensors” and “selected AQI source sensor”.

Use Prompt 1 first, test it, then use Prompt 2.

Prompt 1 — Chart mode layout, Networks, Chart range, sensor chips

You are working in the UK AQ repo on `hex_map.html`.
Please make a focused chart-mode layout update. Do not refactor unrelated code, do not change data files, and do not change anything outside `hex_map.html` unless absolutely necessary.
## Context
The page has two chart-mode paths:
- UK / constituency chart mode
- Countries & Regions / local authority chart mode
Apply all changes consistently to both.
The latest `hex_map.html` already has chart mode, selected sensor symbols, chart tooltip work, and a bottom sensor list. Please inspect the existing implementation before editing.
Relevant areas to inspect:
- `hex-chart-mode-panel`
- `hex-chart-mode-header`
- `hex-chart-mode-title`
- `hex-chart-mode-title-block`
- `hex-chart-mode-reading`
- `hex-chart-mode-controls`
- `uk-hex-chart-window`
- `cr-hex-chart-window`
- `chart-back-to-map`
- `window-stepper`
- `pollutant-selector`
- `networks-pill-anchor`
- `uk-networks-pill-anchor`
- `cr-networks-pill-anchor`
- `.map-canvas-wrap.chart-mode .networks-pill-anchor`
- `body.hex-chart-mode .networks-panel-floating`
- `selectedChartSensorIds`
- `chart-mode-sensor-symbol-svg`
- `renderHexChart`
- `updateHexChartModeHeader`
- `getChartModeContext`
- chart-mode sensor selection/rendering functions
## Goal
In chart mode:
1. Move `Chart range` into the main toolbar row, next to `Window`.
2. Show the Networks dropdown/pill in the same top-right overlay position it uses in map mode.
3. Replace the current chart title/subtitle area with compact selected-sensor chips.
4. Do not repeat the selected area name above the chart.
5. Reduce whitespace so the chart moves up.
6. Keep the bottom sensor list behaviour unchanged.
## Required change 1: Move Chart range into the main toolbar
Move the chart range selector out of the chart panel header and into the main top toolbar.
The toolbar should conceptually read:
```text
Back to Hex Map | Pollutant | Window | Chart range                         Live | Refresh

Requirements:

* Place Chart range directly after the existing Window control.
* It should only be visible in chart mode.
* In map mode, the toolbar should look as it does now.
* Use the existing chart range options:
    * Last 12 hours
    * Last 24 hours
    * Last 7 days
    * Last 31 days
    * Last 90 days
* Reuse the existing chart range state and behaviour if possible.
* Do not leave a second visible Chart range selector in the chart header.
* Remove or hide the old chart-panel Chart range control so it no longer consumes vertical space.
* Keep the Chart range select accessible with a visible label and accessible name.

Implementation guidance:

A reasonable toolbar structure would be something like:

<div class="toolbar-divider chart-mode-only"></div>
<label class="chart-range-toolbar chart-mode-only">
  <span class="field-label">Chart range</span>
  <select>...</select>
</label>

Use existing class naming conventions where possible.

Required change 2: Show Networks dropdown in chart mode

The Networks pill currently appears in the canvas top-right overlay area in map mode, not in the toolbar.

In chart mode:

* Show the Networks pill in the same top-right overlay position it uses in map mode.
* Do not move Networks into the toolbar.
* Do not put Networks next to Live/Refresh.
* Keep Live and Refresh visible in the toolbar.
* The user must be able to open the Networks dropdown and change network selection while remaining in chart mode.
* Changing networks should update the chart, selected sensor chips, and bottom sensor list consistently using the existing network filter behaviour.

Current CSS may hide it with something like:

.map-canvas-wrap.chart-mode .networks-pill-anchor,
body.hex-chart-mode .networks-panel-floating {
  display: none !important;
}

Remove or narrow those rules so the Networks pill and panel work in chart mode.

Keep map-mode Networks behaviour unchanged.

Required change 3: Replace chart title/subtitle with selected-sensor chips

Do not show the selected area name above the chart. The selected area name is already shown in the bottom sensor list header.

Instead, show a compact selected-sensor chip grid above the chart.

The chips should represent the currently selected chart sensors, up to the existing maximum of 4.

Chip layout

Use 2 columns on desktop/wide layouts.

Examples:

[■ Serpentine Gallery · Breathe London   ● 15.4 µg/m³  09:00]   [◆ Science Museum · Breathe London   ● 16.3 µg/m³  10:00]
[● Sloane Street · Breathe London        ● 17.5 µg/m³  10:00]   [▲ St Barnabas... · Breathe London   ● 14.5 µg/m³  10:00]

On narrower screens, collapse to 1 column.

Chip content

Each chip must contain:

{chart symbol} {sensor name} · {network name}   {AQ coloured dot} {value & unit}   {updated time}

Do not include:

* selected area name
* pollutant name
* the word Updated
* the word Value
* the word Timestamp

The pollutant is already clear from the toolbar and y-axis.

Date/time format

For the sensor chip timestamp:

* If the reading is from today, show only HH:MM.
* If the reading is not from today, show DD/MM/YYYY HH:MM.
* Use a 24-hour clock.

Examples:

09:00
26/05/2026 23:00

Value format

For the chip reading:

* Show value and unit only.
* Example: 15.4 µg/m³.
* Do not include the pollutant label.

AQ coloured dot

Each chip must include a small AQ coloured dot before the value.

Requirements:

* Dot colour must match the value/AQ colour for that sensor reading.
* Reuse existing colour/value helpers where possible.
* Do not invent a new unrelated colour scale.

Chart symbol

Each chip must start with the same chart symbol shape used for that sensor’s chart line and sensor list.

Requirements:

* Reuse existing chart symbol rendering helper if possible.
* Do not change line chart symbol size.
* The chip symbol should visually match the selected sensor’s chart symbol.

Chip visual style

Use compact white chips.

Style requirements:

background: #fff;
border: none;
border-radius: 8px;
padding: 5px 8px;
box-shadow: none;

or equivalent.

Additional requirements:

* No visible border.
* No heavy card treatment.
* Small gaps between chips.
* Text truncates gracefully.
* Sensor name should be most prominent.
* Network name should be muted/secondary.
* Value and time should remain readable.
* The chip area should be labelled accessibly, e.g. Selected chart sensors.

Suggested CSS direction:

.hex-chart-selected-sensors {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 8px;
}
.hex-chart-selected-sensor-chip {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 6px;
  min-width: 0;
  background: #fff;
  border: 0;
  border-radius: 8px;
  padding: 5px 8px;
  box-shadow: none;
}
@media (max-width: 720px) {
  .hex-chart-selected-sensors {
    grid-template-columns: 1fr;
  }
}

Adjust as needed.

Required change 4: Reduce chart-mode whitespace

After moving Chart range and replacing the title/subtitle with chips:

* Reduce top padding inside .hex-chart-mode-panel.
* Reduce gaps in .hex-chart-mode-panel.
* Remove unused title/header vertical space.
* Move the chart upward.
* Keep enough breathing room that the chips and chart do not feel cramped.

Do not reduce the bottom sensor list height. The bottom list currently shows header + 4 rows and should remain that way.

Required change 5: Keep bottom sensor list behaviour unchanged

Do not break the bottom sensor list.

Requirements:

* It should still show the selected area header.
* It should still show selected sensors with symbols and selector buttons.
* It should still allow selecting/deselecting up to 4 chart sensors.
* It should still scroll when needed.
* Existing selected-row highlighting should remain.
* Existing sorting behaviour should remain.
* The selected-sensor chips above the chart must update when selected sensors change.

Behaviour details

* 1 selected sensor: show 1 chip.
* 2 selected sensors: show 2 chips, side-by-side on desktop.
* 3 selected sensors: show 3 chips in the 2-column grid.
* 4 selected sensors: show all 4 chips in a 2x2 grid.
* If the current code auto-selects a sensor when entering chart mode, preserve that behaviour.
* If network filters remove a selected sensor, use existing cleanup behaviour if present; otherwise ensure stale chips do not remain.

Acceptance checks

Please manually verify:

UK chart mode

1. Open chart mode for a UK area with several sensors.
2. Confirm the selected area name is no longer repeated above the chart.
3. Confirm Chart range is in the main toolbar next to Window.
4. Confirm the old chart-header Chart range control is no longer visible.
5. Confirm Networks pill is visible in the canvas top-right overlay, in the same place as map mode.
6. Open Networks dropdown in chart mode and change selection.
7. Confirm chart/list/chips update consistently after changing networks.
8. Select up to 4 sensors.
9. Confirm all selected sensors appear as compact white rounded chips above the chart.
10. Confirm each chip contains chart symbol, sensor name, network name, AQ coloured dot, value/unit, and compact update time.
11. Confirm no chip contains pollutant name, Value, Timestamp, or Updated.
12. Confirm not-today timestamps show DD/MM/YYYY HH:MM.
13. Confirm today timestamps show HH:MM.
14. Confirm chart is moved upward and whitespace is reduced.
15. Confirm bottom sensor list still shows header + 4 rows and behaves as before.

Countries & Regions chart mode

Repeat the same checks in Countries & Regions chart mode.

Regression checks

1. Return to map mode.
2. Confirm map-mode toolbar still looks as before.
3. Confirm map-mode Networks pill still appears in the same place as before.
4. Confirm map-mode sensor list still works.
5. Confirm Live and Refresh still work in both map and chart mode.

Please summarise:

* files changed
* CSS selectors added/changed
* JS functions changed
* behaviours manually verified

---
## Prompt 2 — AQI band source selection using sensor chips
```md
You are working in the UK AQ repo on `hex_map.html`.
This prompt assumes the chart-mode layout has already been updated so that chart mode shows selected-sensor chips above the chart.
Please add an explicit AQI/DAQI/EAQI source sensor selection. Do not refactor unrelated code, do not change data files, and do not change anything outside `hex_map.html` unless absolutely necessary.
## Context
The chart can show up to 4 selected sensors, but the DAQI/EAQI bands currently represent only one sensor. The UI needs to make it clear which selected sensor controls the DAQI/EAQI bands, and allow the user to change it.
Apply this consistently to both:
- UK / constituency chart mode
- Countries & Regions / local authority chart mode
## Goal
1. Clicking a selected-sensor chip chooses that sensor as the DAQI/EAQI band source.
2. The selected AQI-source chip gets a light-blue selected background.
3. The DAQI/EAQI bands area shows the selected sensor’s chart symbol to the left of `DAQI` and `EAQI`.
4. Do not add an internal `AQI` chip or `AQI bands` text inside the sensor chip.
5. Use existing hover/focus UI language: slight lift and halo on clickable chips.
## Required behaviour
### 1. AQI source sensor state
Add or reuse chart-mode state for the selected AQI source sensor.
Requirements:
- The AQI source must be one of the currently selected chart sensors.
- Default AQI source should be the first selected chart sensor, unless existing code already has a sensible default.
- If the user clicks another selected-sensor chip, that sensor becomes the AQI source.
- If the AQI source sensor is deselected, removed, or filtered out by network selection, fall back to the first remaining selected chart sensor.
- Do not leave stale AQI state pointing to a sensor that is not currently charted.
- Preserve existing chart sensor selection behaviour.
Suggested state name:
```js
selectedAqiSensorId

or similar, following existing code style.

2. Make selected-sensor chips clickable for AQI source

Each selected-sensor chip should act as a button for selecting the DAQI/EAQI source.

Requirements:

* Whole chip should be clickable.
* Cursor should be pointer.
* Keyboard accessible:
    * Tab focusable.
    * Enter/Space selects the chip as the AQI source.
* Use accessible state:
    * aria-pressed="true" on the selected AQI-source chip, or
    * aria-current="true" if that fits better.
* Accessible label should explain the action, e.g. Use Serpentine Gallery for DAQI and EAQI bands.

Do not make the chip select/deselect chart sensors. Sensor selection/deselection remains in the bottom sensor list.

3. Selected chip visual state

The chip that controls DAQI/EAQI should use a light-blue selected background.

Use existing UK AQ selected styling if possible:

background: var(--ukaq-control-selected-bg);

or:

background: color-mix(in oklab, var(--accent) 9%, white);

Requirements:

* No border.
* No internal AQI label/chip.
* The selected background should be obvious but not heavy.
* Non-selected chips remain white.
* Hover/focus should still work on all selectable chips.

4. Hover/focus clickable styling

Use the existing site pattern for clickable controls:

* slight lift
* halo/shadow
* no heavy border

Example style direction:

.hex-chart-selected-sensor-chip[role="button"]:hover {
  transform: translateY(-1px);
  box-shadow: var(--ukaq-control-hover-shadow);
}
.hex-chart-selected-sensor-chip[role="button"]:focus-visible {
  outline: 2px solid rgba(60, 120, 172, 0.45);
  outline-offset: 2px;
}

Adjust selector names to match the implementation.

5. Show selected sensor symbol next to DAQI/EAQI bands

The DAQI/EAQI bands area should show the selected AQI source sensor’s chart symbol to the left of the DAQI/EAQI labels.

Desired label style:

■  DAQI  EAQI

Do not use the phrase AQI bands.

Requirements:

* The symbol must match the selected AQI source sensor’s chart symbol.
* The symbol should update when the AQI source changes.
* The symbol should appear to the left of the DAQI and EAQI band labels/rows.
* The label should remain compact.
* Do not add the selected sensor name here; the selected chip already shows it.
* Do not add AQI bands text.

If DAQI and EAQI are separate rows, place the symbol in a small shared label/header area to the left of them, or align it so it clearly indicates both DAQI and EAQI use that selected sensor.

6. DAQI/EAQI data update

When the AQI source changes:

* DAQI/EAQI bands should update to that sensor’s AQI data.
* The line chart itself should continue to show all selected chart sensors.
* Tooltips and chart lines should remain unchanged.
* Bottom sensor list selection should remain unchanged.

If current code calculates DAQI/EAQI from a “primary” or first selected sensor, replace that source with the explicit AQI source sensor.

Visual example

Selected sensor chips:

[■ Serpentine Gallery · Breathe London   ● 15.4 µg/m³  09:00]   ← light blue background
[◆ Science Museum · Breathe London       ● 16.3 µg/m³  10:00]   ← white
[● Sloane Street · Breathe London        ● 17.5 µg/m³  10:00]   ← white
[▲ St Barnabas... · Breathe London       ● 14.5 µg/m³  10:00]   ← white

DAQI/EAQI label/header:

■  DAQI  EAQI

When the user clicks the Science Museum chip:

* Science Museum chip becomes light blue.
* Serpentine Gallery chip returns to white.
* The DAQI/EAQI label symbol changes to ◆.
* DAQI/EAQI bands use Science Museum as their source.
* The line chart still shows all selected sensors.

Constraints

* Do not add an AQI pill inside the sensor chip.
* Do not show the phrase AQI bands.
* Do not add the selected area name above the chart.
* Do not change the chart sensor selection limit.
* Do not change the bottom sensor list selection behaviour.
* Do not remove Live/Refresh.
* Do not move the Networks dropdown.
* Keep implementation contained to hex_map.html.

Acceptance checks

Please manually verify:

UK chart mode

1. Open chart mode for an area with at least 2 selectable sensors.
2. Select 2–4 sensors.
3. Confirm all selected sensor chips are visible.
4. Confirm exactly one chip has the light-blue selected background for DAQI/EAQI source.
5. Confirm the selected chip has no internal AQI label or chip.
6. Confirm hovering a chip gives the standard clickable lift/halo.
7. Confirm keyboard focus works on chips.
8. Confirm Enter/Space selects a chip as the DAQI/EAQI source.
9. Click a different chip.
10. Confirm the selected background moves to that chip.
11. Confirm the DAQI/EAQI symbol changes to that chip’s chart symbol.
12. Confirm the DAQI/EAQI bands update to that sensor.
13. Confirm the line chart still displays all selected sensors.
14. Confirm the bottom sensor list selection does not change when clicking chips.
15. Deselect the AQI-source sensor in the bottom list.
16. Confirm AQI source falls back to another selected sensor and no stale state remains.
17. Change Networks selection so a selected sensor disappears.
18. Confirm chips, chart lines, and DAQI/EAQI source remain consistent.

Countries & Regions chart mode

Repeat the same checks in Countries & Regions chart mode.

Regression checks

1. Confirm map mode still works.
2. Confirm chart tooltips still work.
3. Confirm bottom sensor list sorting still works.
4. Confirm Chart range still works.
5. Confirm Networks dropdown still works in chart mode and map mode.

Please summarise:

* files changed
* state variables added/changed
* CSS selectors added/changed
* JS functions changed
* behaviours manually verified

This is definitely safer in two phases: **Prompt 1 gets the layout right**, then **Prompt 2 adds AQI-source behaviour without mixing it into the layout work**.